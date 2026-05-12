# Dokumentasi Alur dan Struktur Proyek: Transaction Fraud Monitoring System

Dokumen ini merangkum keseluruhan struktur, arsitektur, dan alur kerja (flow) dari proyek **Transaction Fraud Monitoring System**. Rangkuman ini dikompilasi dari berbagai dokumen perencanaan dan spesifikasi teknis untuk memberikan pandangan menyeluruh (helicopter view) yang dapat digunakan sebagai bahan laporan atau referensi utama proyek.

---

## 1. Gambaran Umum (Overview)

Proyek ini adalah sebuah **full-stack production ML system** untuk memantau dan mendeteksi penipuan (fraud) pada transaksi secara *end-to-end* dan *real-time*. Sistem ini memanfaatkan model **XGBoost** untuk prediksi probabilitas fraud dan menampilkan hasilnya melalui dashboard interaktif.

**Teknologi Utama (Tech Stack):**
*   **Machine Learning**: Python, Scikit-Learn, XGBoost, Pandas.
*   **Backend API**: FastAPI, Pydantic, Uvicorn.
*   **Database**: PostgreSQL (untuk produksi) / SQLite (untuk pengembangan).
*   **Frontend**: Next.js, React (menggunakan App Router dan Tailwind/Vanilla CSS dengan dark theme).
*   **AI Agent**: OpenAI (Gemini) API dengan arsitektur RAG (Retrieval-Augmented Generation).

---

## 2. Dataset dan Fitur (Features)

Sistem ini menganalisis transaksi menggunakan model Machine Learning yang dilatih pada dataset (`credit_fraud.csv`). Fitur-fitur utama yang digunakan dalam prediksi meliputi:

*   **age**: Usia pemilik akun.
*   **transaction_amount**: Jumlah nominal transaksi.
*   **account_balance**: Saldo akun sebelum transaksi.
*   **num_transactions_today**: Jumlah transaksi hari ini.
*   **is_foreign_transaction**: Indikator transaksi luar negeri.
*   **transaction_hour**: Waktu/jam transaksi (0-23).
*   **prev_fraud_flag**: Riwayat fraud sebelumnya.
*   **merchant_distance_km**: Jarak lokasi merchant dengan pengguna.
*   **merchant_risk_score**: Skor risiko merchant (0-10).
*   **is_fraud** (Target): Indikator penipuan (0 = Normal, 1 = Fraud).

Sistem ML Pipeline juga secara otomatis menangani *dirty data* (seperti usia negatif, format yang salah) dan melakukan imputasi untuk *missing values* menggunakan algoritma XGBoost Imputer.

---

## 3. Arsitektur Sistem

Sistem terdiri dari empat komponen utama yang saling terhubung:

```mermaid
graph TB
    subgraph "Frontend - Next.js"
        A["🧑 Nasabah Form<br/>Input Transaksi"] 
        B["📊 Bank Dashboard<br/>Analytics & Insights"]
        C["📋 Monitoring Page<br/>Approve/Reject Transaksi"]
        D["🤖 Chatbot Widget<br/>AI Agent + RAG"]
    end
    
    subgraph "Backend - FastAPI"
        E["🔮 /predict<br/>Fraud Prediction API"]
        F["📈 /dashboard<br/>Analytics API"]
        G["💬 /chat<br/>Chatbot Agent API"]
        H["📝 /transactions<br/>CRUD API"]
    end
    
    subgraph "ML & Data"
        I["🧠 XGBoost Pipeline<br/>Trained Model (.joblib)"]
        J["🗄️ SQLite Database<br/>Transactions Store"]
        K["📚 RAG Knowledge Base<br/>JSON Documents"]
    end

    A -->|POST transaksi| E
    B -->|GET stats| F
    C -->|GET/PATCH| H
    D -->|POST message| G
    E --> I
    F --> J
    G -->|1. retrieve context| K
    G -->|2. tool calls| H
    H --> J
    E -->|save result| J
```

1.  **Frontend (Next.js)**: Menyediakan antarmuka untuk Nasabah (input transaksi) dan Petugas Bank (dashboard analytics, monitoring table, chatbot).
2.  **Backend (FastAPI)**: Menyediakan REST API endpoints (`/predict`, `/dashboard`, `/transactions`, `/chat`).
3.  **Machine Learning**: Model XGBoost yang telah dilatih dan dibungkus dalam pipeline `.joblib` untuk dieksekusi oleh backend saat ada permintaan `/predict`.
4.  **RAG Knowledge Base**: Dokumen JSON yang menyimpan informasi domain fraud, kapabilitas sistem, dan panduan alat (tool guides) yang diakses oleh AI Chatbot.

---

## 4. Alur Kerja (System Flow)

Berikut adalah detail dari masing-masing alur proses di dalam sistem:

### A. Alur Transaksi Nasabah

```mermaid
flowchart TD
    A["Nasabah membuka<br/>halaman Transaction Form"] --> B["Mengisi form transaksi<br/>(amount, age, merchant, dll)"]
    B --> C["Klik Submit"]
    C --> D["Frontend mengirim<br/>POST /api/predict"]
    D --> E["FastAPI menerima data"]
    
    E --> F["Pipeline: FraudDataCleaner<br/>Bersihkan data kotor"]
    F --> G["Pipeline: XGBPredictiveImputer<br/>Isi missing values"]
    G --> H["Pipeline: FraudFeatureEngineer<br/>Buat fitur baru"]
    H --> I["Pipeline: StandardScaler<br/>Normalisasi fitur"]
    I --> J["Pipeline: XGBClassifier<br/>Prediksi fraud probability"]
    
    J --> K["Simpan transaksi +<br/>probability ke SQLite"]
    K --> L{"Fraud Probability?"}
    
    L -->|"> 80%"| M["🔴 HIGH RISK<br/>Status: Pending Review"]
    L -->|"50% - 80%"| N["🟡 MEDIUM RISK<br/>Status: Pending Review"]
    L -->|"< 50%"| O["🟢 LOW RISK<br/>Status: Auto-Approved"]
    
    M --> P["Tampilkan hasil ke<br/>Nasabah dengan gauge meter"]
    N --> P
    O --> P
    
    P --> Q["Transaksi muncul di<br/>Monitoring Page bank"]

    style M fill:#dc3545,color:#fff
    style N fill:#ffc107,color:#000
    style O fill:#28a745,color:#fff
```

1.  Nasabah membuka **Transaction Form** di frontend.
2.  Nasabah mengisi form (amount, merchant, age, dll) dan melakukan submit.
3.  Frontend mengirimkan request `POST /api/predict` ke backend FastAPI.
4.  Data melewati **ML Pipeline** (Pembersihan Data → Imputasi → Feature Engineering → Normalisasi → Klasifikasi menggunakan XGBoost).
5.  Model mengembalikan **Fraud Probability**. Hasil diklasifikasikan menjadi:
    *   **🔴 HIGH RISK** (> 80%): Membutuhkan tinjauan (Pending Review).
    *   **🟡 MEDIUM RISK** (50% - 80%): Membutuhkan tinjauan (Pending Review).
    *   **🟢 LOW RISK** (< 50%): Disetujui otomatis (Auto-Approved).
6.  Transaksi beserta probabilitasnya disimpan ke Database.
7.  Frontend menampilkan *gauge meter* animasi yang menunjukkan level risiko kepada nasabah.

### B. Alur Dashboard dan Monitoring Bank

```mermaid
flowchart TD
    A["Petugas Bank login<br/>ke Dashboard"] --> B{"Pilih halaman?"}
    
    B -->|Dashboard| C["GET /api/dashboard/stats"]
    C --> D["Tampilkan KPI Cards<br/>Total Tx, Fraud Rate,<br/>Approved, Rejected"]
    D --> E["Render Charts<br/>Fraud by Hour, Amount Dist,<br/>Risk Score Analysis"]
    E --> F["Auto-refresh<br/>setiap 30 detik"]
    
    B -->|Monitoring| G["GET /api/transactions<br/>?status=pending"]
    G --> H["Tampilkan tabel transaksi<br/>Color-coded by risk"]
    H --> I{"Petugas mengambil<br/>keputusan?"}
    
    I -->|Approve ✅| J["PATCH /api/transactions/id<br/>status = approved"]
    I -->|Reject ❌| K["PATCH /api/transactions/id<br/>status = rejected"]
    I -->|Butuh bantuan AI| L["Buka Chatbot Widget"]
    
    J --> M["Update database<br/>& refresh tabel"]
    K --> M
    L --> N["Chatbot Agent Flow"]
```

1.  Petugas Bank login dan mengakses **Dashboard** atau **Monitoring Page**.
2.  Pada Dashboard (`GET /api/dashboard/stats`), sistem menampilkan KPI (Total Transaksi, Tingkat Penipuan/Fraud Rate) dan grafik (Distribusi Fraud per Jam, Skor Risiko) yang *auto-refresh* setiap 30 detik.
3.  Pada Monitoring Page (`GET /api/transactions`), sistem menampilkan tabel berisi seluruh transaksi, dengan kode warna berdasarkan tingkat risiko.
4.  Petugas Bank dapat melakukan aksi **Approve** atau **Reject** terhadap transaksi yang berstatus "pending". Ini akan mengubah status transaksi di database via request `PATCH`.

### C. Alur AI Chatbot (Agent dengan RAG)

**1. Alur Chatbot Agent + RAG**
```mermaid
flowchart TD
    A["Petugas mengetik pesan<br/>di Chatbot Widget"] --> B["Frontend POST /api/chat<br/>message + session_id"]
    
    B --> C["Backend menerima pesan"]
    
    C --> D["Step 1: INTENT CLASSIFICATION<br/>Cocokkan pesan dengan<br/>RAG Knowledge Base"]
    
    D --> E{"Intent terdeteksi?"}
    
    E -->|Ya - Match ditemukan| F["Ambil context document<br/>yang relevan dari RAG"]
    E -->|Tidak - Diluar scope| G["Respond: Maaf, saya hanya<br/>bisa membantu terkait<br/>monitoring fraud transaksi"]
    
    F --> H["Step 2: BUILD PROMPT<br/>System Prompt + RAG Context<br/>+ User Message + Tools"]
    
    H --> I["Step 3: SEND TO GEMINI<br/>Prompt yang sudah diperkaya<br/>context dari RAG"]
    
    I --> J{"Gemini response<br/>type?"}
    
    J -->|Tool Call| K["Execute tool function<br/>(query DB, approve, reject)"]
    K --> L["Kirim tool result<br/>kembali ke Gemini"]
    L --> I
    
    J -->|Text Response| M["Return response<br/>ke frontend"]
    
    M --> N["Tampilkan di<br/>chat bubble"]
    G --> N

    style G fill:#dc3545,color:#fff
    style F fill:#28a745,color:#fff
```

**2. Detail RAG Pipeline**
```mermaid
flowchart LR
    subgraph "Knowledge Base (JSON files)"
        KB1["📄 system_capabilities.json<br/>Apa saja yang bisa dilakukan agent"]
        KB2["📄 fraud_domain.json<br/>Penjelasan fitur, threshold,<br/>istilah fraud detection"]
        KB3["📄 tool_guides.json<br/>Cara penggunaan setiap tool<br/>beserta contoh perintah"]
        KB4["📄 faq.json<br/>Pertanyaan umum dan<br/>jawaban standar"]
    end
    
    subgraph "RAG Retriever"
        R1["User Message masuk"]
        R2["Keyword Matching +<br/>TF-IDF Similarity"]
        R3["Top-K relevant<br/>documents retrieved"]
    end
    
    subgraph "Prompt Builder"
        P1["System Prompt<br/>(fixed, minimal)"]
        P2["RAG Context<br/>(dynamic, relevant only)"]
        P3["Tool Definitions<br/>(filtered by intent)"]
        P4["Final Prompt<br/>ke Gemini API"]
    end
    
    R1 --> R2
    R2 --> KB1 & KB2 & KB3 & KB4
    R2 --> R3
    
    P1 --> P4
    R3 --> P2 --> P4
    P3 --> P4
```

1.  Petugas Bank bertanya/meminta aksi melalui **Chat Widget** (contoh: "Setujui semua transaksi low risk").
2.  Pesan dikirim melalui `POST /api/chat`.
3.  Sistem backend melakukan pencarian (*retrieval*) dokumen konteks yang relevan dari **RAG Knowledge Base** (menggunakan TF-IDF Similarity).
4.  Prompt dibangun dengan menyertakan Konteks RAG + Tool Definitions + Pesan User.
5.  Prompt dikirim ke LLM (Gemini/OpenAI API).
6.  LLM dapat merespons dengan teks atau dengan mengeksekusi alat (Tool Call) seperti `approve_transaction`.
7.  Hasil eksekusi dikirim kembali ke LLM untuk menghasilkan jawaban final yang kemudian ditampilkan ke pengguna di widget chat.

### D. End-to-End Data Flow Sequence

Berikut adalah urutan waktu (sequence) seluruh komponen sistem bekerja dari mulai nasabah hingga petugas bank menggunakan chatbot:

```mermaid
sequenceDiagram
    participant N as Nasabah
    participant FE as Frontend (Next.js)
    participant API as FastAPI Backend
    participant ML as XGBoost Pipeline
    participant DB as SQLite Database
    participant RAG as RAG Knowledge Base
    participant LLM as Gemini API
    participant B as Petugas Bank

    Note over N,B: === FLOW 1: Nasabah Submit Transaksi ===
    N->>FE: Isi form transaksi
    FE->>API: POST /api/predict {data}
    API->>ML: pipeline.predict_proba(data)
    ML-->>API: fraud_probability: 0.87
    API->>DB: INSERT transaction (prob=0.87, status=pending)
    API-->>FE: {probability: 0.87, risk: "HIGH"}
    FE-->>N: Tampilkan gauge meter (merah)
    
    Note over N,B: === FLOW 2: Bank Monitoring ===
    B->>FE: Buka Monitoring Page
    FE->>API: GET /api/transactions?status=pending
    API->>DB: SELECT * WHERE status='pending'
    DB-->>API: [{id:1, prob:0.87, ...}]
    API-->>FE: Transaction list
    FE-->>B: Tabel color-coded
    
    Note over N,B: === FLOW 3: Chatbot Agent + RAG ===
    B->>FE: "Approve semua transaksi fraud < 30%"
    FE->>API: POST /api/chat {message}
    API->>RAG: Retrieve relevant context
    RAG-->>API: Context: tool_guides + capabilities
    API->>LLM: System + RAG Context + Message + Tools
    LLM-->>API: tool_call: approve_low_risk(threshold=0.3)
    API->>DB: UPDATE status='approved' WHERE prob < 0.3
    DB-->>API: 12 rows updated
    API->>LLM: Tool result: 12 transaksi di-approve
    LLM-->>API: "Selesai! 12 transaksi dengan fraud probability di bawah 30% telah di-approve."
    API-->>FE: Chat response
    FE-->>B: Tampilkan di chat bubble
```

---

## 5. Desain Antarmuka (UI/UX)

Sistem menggunakan pendekatan desain premium **Dark Theme** dengan elemen **Glassmorphism** untuk kesan modern. 

*   **Warna Utama**: Navy sangat gelap untuk *background*, teks terang, dengan aksen *Indigo*.
*   **Kode Warna Status**: Hijau (Aman/Disetujui), Kuning (Peringatan/Pending), Merah (Bahaya/Ditolak).
*   **Struktur Halaman**:
    *   `/`: **Landing Page** (Gateway menuju form nasabah atau dashboard bank).
    *   `/transaction`: **Form Transaksi** (Dilengkapi dengan animasi *Gauge Meter* hasil prediksi).
    *   `/dashboard`: **Dashboard Analitik** (Berisi *KPI Cards* dan grafik *Chart.js*).
    *   `/monitoring`: **Halaman Monitoring** (Tabel interaktif transaksi dengan tombol aksi persetujuan).
    *   **Chat Widget**: Tombol asisten mengambang (*floating*) yang dapat diakses secara global untuk bantuan interaktif.

---

## 6. Struktur Direktori Proyek

```text
fraud_detection/
├── ml-service/                 # ML & Backend API Service (FastAPI)
│   ├── app/                    # File utama aplikasi API (main.py, database.py, chatbot.py)
│   ├── knowledge/              # RAG Knowledge Base (.json)
│   ├── model/                  # Artefak model pipeline (.joblib)
│   └── train_and_save.py       # Script pelatihan ML
├── frontend/                   # Frontend Web (Next.js)
│   └── src/app/                # Komponen halaman UI (transaction, dashboard, monitoring)
├── src/                        # Source Code ML Engine (Feature Engineering, dll)
├── README.md                   # Setup Guide
└── feature.md                  # Dokumentasi fitur ML
```

---

## 7. Rencana Pelaksanaan (Execution Plan)

Pembangunan sistem dilakukan secara bertahap (Phased Approach):
1.  **Phase 1 — ML Backend**: Pelatihan model XGBoost, pembuatan endpoint FastAPI, dan integrasi dengan database.
2.  **Phase 2 — Frontend Foundation**: Setup Next.js, pembuatan *design system*, dan layout dasar.
3.  **Phase 3 — Nasabah Form**: Implementasi halaman pengisian transaksi dan animasi hasil prediksi.
4.  **Phase 4 — Bank Dashboard**: Pembuatan analitik dan visualisasi data.
5.  **Phase 5 — Monitoring Page**: Pembuatan tabel ulasan transaksi dan fitur tindakan.
6.  **Phase 6 & 7 — AI Chatbot**: Pembangunan basis pengetahuan RAG dan integrasi LLM Agent untuk widget asisten.
