# ✈️ PaperPilot — RAG Document Q&A Assistant

Chatbot AI berbasis **Retrieval-Augmented Generation (RAG)** yang bisa menjawab
pertanyaan berdasarkan isi dokumen PDF yang kamu upload. Dibangun dengan
**LangChain** + **Google Gemini API**, UI pakai **Streamlit**.

> Versi lanjutan dari eksperimen sebelumnya di Langflow (no-code) — kali ini
> dibangun ulang dari nol pakai kode agar lebih fleksibel dan powerful.

## Use Case
Target pengguna: mahasiswa, peneliti, atau siapa saja yang perlu memahami
dokumen panjang (laporan, paper, kontrak) dengan cepat lewat tanya-jawab,
tanpa harus membaca semuanya dari awal.

## Fitur Utama (Parameter Kreatif)
| Fitur | Deskripsi |
|---|---|
| **Multi-document RAG** | Upload beberapa PDF sekaligus, tanya lintas dokumen dalam satu sesi |
| **Citation tracking** | Setiap jawaban menyertakan sumber (nama file + nomor halaman + potongan teks asli) |
| **Conversational memory** | Bisa follow-up question ("terus gimana kalau...") tanpa mengulang konteks |
| **Custom chunking** | User bisa atur `chunk size` & `chunk overlap` langsung dari UI untuk eksperimen kualitas retrieval |
| **Anti-halusinasi prompt** | Jika info tidak ada di dokumen, bot jujur bilang tidak ditemukan, tidak mengarang jawaban |

## Arsitektur Singkat
```
PDF Upload → PyPDFLoader → RecursiveCharacterTextSplitter (chunking)
           → GoogleGenerativeAIEmbeddings → FAISS (vector store)
           → ConversationalRetrievalChain (Gemini + memory) → Jawaban + Sumber
```

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
   - Upload 1 atau lebih file PDF di sidebar
   - Klik "Proses dokumen"
   - Mulai tanya-tanya di kolom chat

## Cara Dapat Gemini API Key
1. Buka https://aistudio.google.com/apikey
2. Login dengan akun Google
3. Klik "Create API Key" → pilih/buat project → copy key
4. Tempel ke file `.env` (jangan pernah commit `.env` ke GitHub!)

## Struktur Proyek
```
paperpilot/
├── app.py            # UI Streamlit (upload, chat, tampilan citation)
├── rag_engine.py      # Logic RAG: loading, chunking, embedding, retrieval chain
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Potensi Pengembangan Lanjutan
- Ganti FAISS dengan vector store persisten (Chroma/Pinecone) agar index tidak hilang saat restart
- Tambah dukungan format lain (docx, txt, csv)
- Tambah evaluasi otomatis (RAGAS) untuk mengukur kualitas jawaban vs ground truth
- Highlight langsung di halaman PDF sumber jawaban (bukan cuma snippet teks)
