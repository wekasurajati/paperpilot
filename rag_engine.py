"""
PaperPilot - RAG Document Q&A Assistant
-----------------------------------------
Fitur:
- Multi-document upload (bisa upload beberapa PDF sekaligus, ditanya lintas dokumen)
- Custom chunking (user bisa atur chunk size & overlap dari UI)
- Conversational RAG 
- Citation tracking 
- Anti-halusinasi prompt 
- Local disk cache per dokumen (file yang sama + setting chunking yang sama gak
  di-embed ulang, hemat kuota API)

Stack: LangChain + Google Gemini (LLM) + local HuggingFace embeddings + FAISS (vector store)

"""

import hashlib
import os
import time
from dataclasses import dataclass, field
 
# Some Anaconda/Windows setups leave a stale SSL_CERT_FILE env var pointing to a
# certificate file that no longer exists, which crashes any library that makes
# HTTPS requests (e.g. huggingface_hub downloading the embedding model). Force
# it to a known-good certificate bundle before anything else runs.
try:
    import certifi
 
    _cert_path = os.environ.get("SSL_CERT_FILE")
    if not _cert_path or not os.path.isfile(_cert_path):
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except ImportError:
    pass
 
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
 
load_dotenv()
 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")
# Free, local embedding model (runs on CPU, no API key, no quota). Downloaded once
# from HuggingFace (~90MB) and cached locally after that.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".faiss_cache")
 
# ---------- Prompt anti-halusinasi + citation-aware (general-purpose: adapts
# to whatever document(s) the user uploads, not hardcoded to one topic) ----------
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question", "chat_history"],
    template="""You are PaperPilot, an assistant that answers questions strictly based on the
uploaded document(s) provided below. The document(s) can be about any topic (a research
report, a business plan, a contract, an article, lecture notes, etc.) — infer the subject
matter from the context itself, and do not assume a fixed domain.
 
Previous conversation:
{chat_history}
 
Relevant context retrieved from the document(s) (each chunk is labeled with
[Source: file_name, page: x]):
{context}
 
Instructions:
- Answer ONLY using the context provided above. Do not use outside knowledge or make
  assumptions beyond what is explicitly stated in the context.
- If the context is not sufficient to answer the question, honestly say the information
  is not available in the document(s). Never guess or fabricate an answer.
- Answer in the same language the question was asked in (respond in Indonesian if the
  question is in Indonesian, in English if it's in English, etc.).
- Answer clearly and concisely. Use bullet points or numbered lists when presenting
  multiple facts, metrics, categories, or steps, so the answer is easy to scan.
- Include specific figures, numbers, names, or quotes from the context when they are
  relevant to the question — don't be vague when the document has exact details.
- Do NOT use LaTeX or math notation (no dollar signs, no backslashes). Write numbers and
  percentages in plain text, e.g. "93 percent" or "K = 4" instead of math symbols.
- When helpful, briefly mention which part or section of the document the answer comes
  from (e.g., "based on the Results section...") — phrase this naturally, don't force it
  if the document has no clear section structure.
- Keep the answer focused on what was asked; avoid restating the entire context or
  repeating information unnecessarily.
- If this is a follow-up question, use the previous conversation above to understand what
  the user is referring to, but still ground your actual answer in the context provided.
 
Question: {question}
Answer:""",
)
 
 
@dataclass
class PaperPilotSession:
    """Menyimpan state satu sesi RAG: vectorstore, chain, memory, dan daftar file yang di-index."""
 
    chunk_size: int = 1000
    chunk_overlap: int = 150
    vectorstore: FAISS = None
    chain: ConversationalRetrievalChain = None
    memory: ConversationBufferMemory = None
    indexed_files: list = field(default_factory=list)
    _merged_keys: set = field(default_factory=set)
 
    _embeddings_cache = None
 
    def _get_embeddings(self):
        # Cached at class level: loading the model from disk takes a couple
        # seconds, so we don't want to reload it on every add_documents() call.
        if PaperPilotSession._embeddings_cache is None:
            PaperPilotSession._embeddings_cache = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        return PaperPilotSession._embeddings_cache
 
    def _get_llm(self):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY belum diset. Isi dulu di file .env.")
        return ChatGoogleGenerativeAI(model=CHAT_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.2)
 
    def _friendly_quota_error(self, e: Exception) -> ValueError:
        """Turn Gemini's raw 429/quota traceback into a clear, actionable message."""
        msg = str(e)
        if "429" in msg or "quota" in msg.lower() or "ResourceExhausted" in msg:
            if "PerDay" in msg or "per day" in msg.lower():
                return ValueError(
                    "Gemini free-tier daily quota has been used up (limit: 1000 requests/day "
                    "for this model). Wait about 24 hours for it to reset, or enable billing "
                    "on your Google AI Studio project for a much higher limit. "
                    "See: https://ai.dev/rate-limit"
                )
            return ValueError(
                "Gemini API rate limit hit (too many requests in a short time). "
                "Wait about a minute and try again."
            )
        return ValueError(f"Something went wrong while talking to Gemini: {msg}")
 
    def _embed_with_retry(self, fn, *args, max_retries: int = 2, **kwargs):
        """Retry once or twice on transient rate limits (NOT on a daily quota cap,
        which won't resolve itself within a short retry window)."""
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                last_err = e
                is_daily_cap = "PerDay" in msg or "per day" in msg.lower()
                if ("429" in msg or "quota" in msg.lower()) and not is_daily_cap and attempt < max_retries:
                    time.sleep(20)
                    continue
                raise self._friendly_quota_error(e) from e
        raise self._friendly_quota_error(last_err)
 
    def _cache_key(self, path: str) -> str:
        with open(path, "rb") as f:
            content_hash = hashlib.md5(f.read()).hexdigest()[:12]
        filename = os.path.basename(path)
        return f"{filename}_{self.chunk_size}_{self.chunk_overlap}_{content_hash}"
 
    def add_documents(self, file_paths: list[str]):
        """Load, chunk, embed, dan tambahkan dokumen baru ke vectorstore (mendukung multi-file).
        Dokumen yang isinya + pengaturan chunking-nya persis sama seperti sebelumnya akan
        di-load dari cache lokal (.faiss_cache) alih-alih di-embed ulang -> hemat kuota API,
        terutama pas development/testing di mana file yang sama sering diupload berkali-kali."""
        embeddings = self._get_embeddings()
        os.makedirs(CACHE_DIR, exist_ok=True)
 
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
 
        # Cache keys already merged into self.vectorstore this session -- reprocessing
        # the same key again would try to insert IDs that already exist and crash FAISS.
        for path in file_paths:
            filename = os.path.basename(path)
            key = self._cache_key(path)
 
            if key in self._merged_keys:
                if filename not in self.indexed_files:
                    self.indexed_files.append(filename)
                continue
 
            cache_path = os.path.join(CACHE_DIR, key)
 
            if os.path.isdir(cache_path):
                store = FAISS.load_local(cache_path, embeddings, allow_dangerous_deserialization=True)
            else:
                loader = PyPDFLoader(path)
                pages = loader.load()  # 1 Document per halaman, metadata sudah ada "page"
                chunks = splitter.split_documents(pages)
                for c in chunks:
                    # Normalisasi metadata biar konsisten buat citation
                    c.metadata["source_file"] = filename
                    c.metadata["page_number"] = c.metadata.get("page", 0) + 1
                store = self._embed_with_retry(FAISS.from_documents, chunks, embeddings)
                store.save_local(cache_path)
 
            self._merged_keys.add(key)
 
            if self.vectorstore is None:
                self.vectorstore = store
            else:
                self.vectorstore.merge_from(store)
 
            if filename not in self.indexed_files:
                self.indexed_files.append(filename)
 
        self._rebuild_chain()
 
    def _rebuild_chain(self):
        if self.memory is None:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True, output_key="answer"
            )
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self._get_llm(),
            retriever=retriever,
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        )
 
    def ask(self, question: str) -> dict:
        if self.chain is None:
            raise ValueError("No documents uploaded yet. Upload a PDF first.")
        try:
            result = self.chain.invoke({"question": question})
        except ValueError:
            raise
        except Exception as e:  # noqa: BLE001
            raise self._friendly_quota_error(e) from e
        sources = []
        for doc in result.get("source_documents", []):
            sources.append(
                {
                    "file": doc.metadata.get("source_file", "unknown"),
                    "page": doc.metadata.get("page_number", "?"),
                    "snippet": doc.page_content[:200].strip() + "...",
                }
            )
        return {"answer": result["answer"], "sources": sources}
 
    def reset(self):
        self.vectorstore = None
        self.chain = None
        self.memory = None
        self.indexed_files = []
        self._merged_keys = set()