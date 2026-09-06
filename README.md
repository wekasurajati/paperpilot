# PaperPilot — RAG Document Q&A Assistant

Chatbot AI berbasis **Retrieval-Augmented Generation (RAG)** yang bisa menjawab
pertanyaan berdasarkan isi dokumen PDF yang kamu upload. Dibangun dengan
**LangChain** + **Google Gemini API**, UI pakai **Streamlit**.

> Versi lanjutan dari eksperimen sebelumnya di Langflow (no-code) — kali ini
> dibangun ulang dari nol pakai kode agar lebih fleksibel dan powerful.

## Use Case

Target pengguna: mahasiswa, peneliti, atau siapa saja yang perlu memahami
dokumen panjang (laporan, paper, kontrak) dengan cepat lewat tanya-jawab,
tanpa harus membaca semuanya dari awal.

## Fitur Utama

| Fitur | Deskripsi |
|---|---|
| Multi-document RAG | Upload beberapa PDF sekaligus, tanya lintas dokumen dalam satu sesi |
| Citation tracking | Setiap jawaban menyertakan sumber (nama file + nomor halaman + potongan teks asli) |
| Conversational memory | Bisa follow-up question tanpa mengulang konteks |
| Custom chunking | User bisa atur chunk size & chunk overlap langsung dari UI |
| Anti-halusinasi prompt | Jika info tidak ada di dokumen, bot bilang tidak ditemukan, tidak mengarang jawaban |
| Local embedding cache | Dokumen yang sama (isi + setting chunking identik) tidak di-embed ulang, disimpan di `.faiss_cache` |

## Arsitektur

```
PDF Upload -> PyPDFLoader -> RecursiveCharacterTextSplitter (chunking)
           -> HuggingFace sentence-transformers (embedding, lokal & gratis)
           -> FAISS (vector store, dengan cache lokal per dokumen)
           -> ConversationalRetrievalChain (Gemini + memory) -> Jawaban + Sumber
```

Embedding (proses "membaca" dokumen menjadi vector) dijalankan lokal dengan
model open-source `sentence-transformers/all-MiniLM-L6-v2`, sehingga proses
indexing dokumen tidak dibatasi kuota API. Bagian yang benar-benar memproses
bahasa alami dan menghasilkan jawaban ke pengguna (LLM) sepenuhnya
menggunakan **Gemini API**.

## Cara Menjalankan (VS Code + Miniconda)

1. Buka folder ini di VS Code.
2. Buat environment conda:
   ```bash
   conda create -n paperpilot python=3.11 -y
   conda activate paperpilot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Salin `.env.example` jadi `.env`, isi API key Gemini kamu:
   ```bash
   cp .env.example .env
   ```
5. Jalankan aplikasi:
   ```bash
   streamlit run app.py
   ```
6. Browser otomatis kebuka di `http://localhost:8501`.
   - Upload satu atau lebih file PDF di sidebar
   - Klik "Process documents"
   - Mulai tanya-tanya di kolom chat

## Konfigurasi (.env)

```
GOOGLE_API_KEY=isi_api_key_kamu_disini
GEMINI_CHAT_MODEL=gemini-3.6-flash
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

`GOOGLE_API_KEY` wajib diisi untuk bagian chat/LLM. `EMBEDDING_MODEL_NAME`
berjalan lokal dan tidak butuh API key.

## Struktur Proyek

```
paperpilot/
├── app.py               # UI Streamlit (upload, chat, citation)
├── rag_engine.py         # Logic RAG: loading, chunking, embedding, retrieval chain
├── requirements.txt
├── .env.example
├── .streamlit/config.toml
├── assets/               # Logo
├── .gitignore
└── README.md
```

## Deployment

Aplikasi ini bisa di-deploy ke Streamlit Community Cloud langsung dari
repository ini. Saat deploy, isi konfigurasi di atas melalui menu
"Secrets" pada dashboard Streamlit Cloud, bukan lewat file `.env`.

## Potensi Pengembangan Lanjutan

- Ganti FAISS dengan vector store persisten (Chroma/Pinecone) agar index tidak hilang saat restart
- Tambah dukungan format lain (docx, txt, csv)
- Tambah evaluasi otomatis (RAGAS) untuk mengukur kualitas jawaban vs ground truth
- Highlight langsung di halaman PDF sumber jawaban, bukan hanya potongan teks