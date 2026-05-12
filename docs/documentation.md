# Dokumentasi Proyek: Fraud Detection Monitoring System

Proyek ini adalah sistem deteksi penipuan (fraud detection) transaksi keuangan berbasis Machine Learning end-to-end. Sistem ini terdiri dari model prediktif Machine Learning, backend REST API (FastAPI), dan antarmuka web interaktif (Next.js), dilengkapi dengan AI Agent cerdas yang dapat mengambil aksi pada database.

---

## 🏗 Arsitektur Sistem

Sistem ini terbagi menjadi tiga komponen utama:

1. **Machine Learning Pipeline (Python / Scikit-Learn / XGBoost)**
   - Bertugas membersihkan data (handling missing values, outliers).
   - Melakukan feature engineering dan scaling.
   - Melatih model XGBoost untuk memprediksi probabilitas fraud dari transaksi baru.

2. **Backend Service (Python / FastAPI / PostgreSQL)**
   - Menyediakan REST API endpoints untuk melayani antarmuka (frontend).
   - Mengelola operasi database PostgreSQL (menyimpan transaksi, mengambil status, menghitung statistik).
   - Menjalankan **AI Agent** yang menggunakan kapabilitas OpenAI *Function Calling*.

3. **Frontend Application (Next.js / React)**
   - Menyediakan UI terpisah untuk dua peran (Role): **Nasabah** (menginput form transaksi) dan **Kreditur/Bank** (dashboard analitik dan monitoring).
   - Mengintegrasikan widget chatbot AI sebagai asisten bank.

---

## ✨ Fitur Utama

### 1. Sistem Prediksi Real-Time
Ketika nasabah memasukkan data transaksi melalui formulir web, data dikirim ke FastAPI, dimasukkan ke dalam pipeline Machine Learning, dan mengembalikan `fraud_probability` beserta `risk_level` (LOW, MEDIUM, HIGH) secara instan.

### 2. Role-Based Interface
- **Halaman Nasabah (`/transaction`)**: Form pengajuan transaksi sederhana yang ramah pengguna.
- **Halaman Bank Dashboard (`/dashboard`)**: Visualisasi analitik (total transaksi, rasio fraud, chart distribusi) untuk pihak bank.
- **Halaman Monitoring (`/monitoring`)**: Tabel interaktif bagi petugas bank untuk melakukan *review* (Approve/Reject) transaksi per baris.

### 3. AI Agent Terintegrasi (Agentic AI)
Sistem memiliki asisten berbasis teks yang terhubung ke model Large Language Model (OpenAI). Agent ini memiliki "Tools" khusus sehingga tidak hanya bisa menjawab pertanyaan, tetapi bisa mengeksekusi instruksi ke database, seperti:
- *"Terima semua transaksi yang nilai risikonya di bawah 0.3"* (`bulk_approve`)
- *"Tolak transaksi dengan risiko di atas 0.8"* (`bulk_reject`)
- *"Buatkan laporan transaksi hari ini"* (`generate_daily_report`)

---

## 📂 Struktur Direktori

```text
fraud_detection/
├── frontend/                     # Aplikasi Web (Next.js)
│   ├── src/app/
│   │   ├── dashboard/            # Halaman Dashboard Bank (Charts & KPI)
│   │   ├── monitoring/           # Halaman Review Transaksi (Approve/Reject)
│   │   ├── transaction/          # Halaman Form Input Nasabah
│   │   ├── layout.js             # Root layout dengan konfigurasi sidebar
│   │   └── page.js               # Landing Page & Pemilihan Role
│   └── src/components/
│       ├── ChatWidget.js         # UI Asisten AI
│       └── Sidebar.js            # Navigasi kiri
│
├── ml-service/                   # Backend API & Machine Learning
│   ├── app/                      # Modul FastAPI
│   │   ├── main.py               # Entry point API (/api/predict, /api/chat, dll)
│   │   ├── database.py           # Konfigurasi PostgreSQL & Query SQL
│   │   ├── agent.py              # Logika AI Agent & Tools OpenAI
│   │   └── model_loader.py       # Pemuat model ML ke memori
│   ├── model/                    # Folder penyimpanan model.pkl / model.joblib hasil training
│   ├── notebook/                 # Eksperimen Data Science (Jupyter Notebooks)
│   └── requirements.txt          # Dependensi Python
│
├── README.md                     # Panduan singkat repository
└── documentation.md              # File dokumentasi ini
```

---

## 🚀 Panduan Instalasi & Menjalankan (Setup Guide)

### 1. Konfigurasi Backend (FastAPI)

1. Masuk ke direktori backend:
   ```bash
   cd ml-service
   ```
2. Buat Virtual Environment dan install dependensi:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Di Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Buat file `.env` di dalam folder `ml-service/` dan isi konfigurasi berikut:
   ```env
   # PostgreSQL Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=fraud_detection
   DB_USER=postgres
   DB_PASSWORD=password_database_anda

   # OpenAI Configuration (Untuk fitur AI Agent)
   OPENAI_API_KEY=sk-proj-xxxx...
   ```
4. Jalankan server backend (Uvicorn):
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   API akan berjalan di `http://localhost:8000`. Anda bisa melihat interaktif dokumentasi API (Swagger) di `http://localhost:8000/docs`.

### 2. Konfigurasi Frontend (Next.js)

1. Buka terminal baru dan masuk ke direktori frontend:
   ```bash
   cd frontend
   ```
2. Install dependensi Node.js:
   ```bash
   npm install
   ```
3. Jalankan development server:
   ```bash
   npm run dev
   ```
4. Buka browser dan navigasikan ke `http://localhost:3000`.

---

## 🛠 Teknologi yang Digunakan

- **Model Machine Learning**: Scikit-Learn, XGBoost, Pandas, Numpy.
- **Backend API**: Python, FastAPI, Pydantic, Uvicorn.
- **Database**: PostgreSQL (Driver: `psycopg2`).
- **AI Agent (LLM)**: OpenAI API (`gpt-4o-mini`).
- **Frontend**: Next.js (App Router), React, CSS (Vanilla Design System), Chart.js.
