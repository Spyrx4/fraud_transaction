# Transaction Fraud Monitoring System

Sistem monitoring penipuan transaksi ujung-ke-ujung (end-to-end) yang terdiri dari Machine Learning Backend untuk memprediksi probabilitas fraud secara real-time dan dashboard untuk memantau transaksi.

---

## 🛠️ Tech Stack
*   **Machine Learning**: Scikit-Learn, XGBoost, Pandas
*   **Backend API**: FastAPI, Pydantic, Uvicorn
*   **Database**: PostgreSQL
*   **Frontend**: Next.js, React (Sedang dalam pengembangan - Phase 2)

---

## 📂 Struktur Direktori Utama
```text
fraud_detection/
├── ml-service/                 # ML & Backend API Service
│   ├── app/                    # FastAPI Application
│   │   ├── main.py             # API Endpoints
│   │   ├── database.py         # PostgreSQL koneksi & CRUD
│   │   └── model_loader.py     # Singleton loader untuk ML pipeline
│   ├── data/                   # Dataset mentah (.csv)
│   ├── model/                  # Model yang sudah dilatih (.joblib)
│   ├── src/                    # Source code pipeline & feature engineering
│   ├── .env                    # Environment variables (Credentials)
│   └── train_and_save.py       # Script untuk melatih & menyimpan model
└── frontend/                   # Frontend Next.js (Coming Soon)
```

---

## 🚀 Panduan Setup & Instalasi (ML Backend)

### 1. Prasyarat (Prerequisites)
Pastikan sistem Anda sudah menginstall:
*   Python 3.10+
*   PostgreSQL 14+

### 2. Konfigurasi Database (PostgreSQL)
Buat database baru di PostgreSQL bernama `fraud_detection`. Anda bisa menggunakan `psql` atau pgAdmin.
```sql
CREATE DATABASE fraud_detection;
```

Buat file `.env` di dalam folder `ml-service/` dan masukkan kredensial PostgreSQL Anda:
```env
DB_HOST=localhost
DB_PORT=5433  # Sesuaikan dengan port PostgreSQL Anda (biasanya 5432)
DB_NAME=fraud_detection
DB_USER=postgres
DB_PASSWORD=password_anda
```

### 3. Install Dependencies
Buka terminal, arahkan ke folder `ml-service`, dan install library yang dibutuhkan:
```bash
pip install fastapi uvicorn pandas numpy scikit-learn xgboost joblib psycopg2 python-dotenv
```

### 4. Latih dan Simpan Model (Training Phase)
Sebelum API bisa berjalan, model harus dilatih menggunakan dataset yang ada.
Jalankan script training:
```bash
cd ml-service
python train_and_save.py
```
**Proses ini akan:**
1. Memuat `credit_fraud.csv`.
2. Melakukan data cleaning & XGBoost imputation.
3. Feature Engineering (menambah fitur baru seperti `tx_balance_ratio`).
4. Menyimpan pipeline utuh ke `ml-service/model/fraud_pipeline.joblib`.

### 5. Jalankan FastAPI Server (Serving Phase)
masuk ke venv terlebih dahulu (Windows CMD/PowerShell):
```bash
venv\Scripts\activate
```

Setelah model tersimpan `.joblib`, jalankan server API:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

API sekarang berjalan di `http://localhost:8000`. 
Untuk melihat **dokumentasi interaktif (Swagger UI)**, buka: `http://localhost:8000/docs`.

---

## 📡 Dokumentasi API Endpoints

Berikut adalah endpoint utama yang disediakan oleh `ml-service`:

| Method | Endpoint | Fungsi |
| :--- | :--- | :--- |
| `GET` | `/` | Health check server. |
| `POST` | `/api/predict` | Menerima data transaksi dari nasabah, memprediksi probabilitas fraud dengan model ML, menyimpannya ke DB, dan mengembalikan hasil (LOW/MEDIUM/HIGH risk). |
| `GET` | `/api/transactions` | Mengambil daftar transaksi (mendukung filter `?status=pending` dan pagination). |
| `PATCH` | `/api/transactions/{id}` | Mengubah status transaksi (contoh: dari `pending` menjadi `approved` atau `rejected`). |
| `GET` | `/api/dashboard/stats` | Mengambil data analitik teragregasi untuk dashboard (fraud rate, transaksi per jam, dll). |

---

## 💻 Frontend (Phase Selanjutnya)
*(Bagian ini akan diupdate setelah Phase 2 selesai)*

Frontend akan dibangun menggunakan **Next.js** dan akan berinteraksi langsung dengan API di atas. Fitur yang direncanakan:
1.  **Form Nasabah**: Halaman untuk mensimulasikan transaksi masuk.
2.  **Dashboard Bank**: Menampilkan grafik statistik dari `/api/dashboard/stats`.
3.  **Monitoring Table**: Menampilkan `/api/transactions` dengan tombol Approve/Reject.
4.  **AI Chatbot Agent**: Menggunakan OpenAI untuk membantu petugas bank mengelola transaksi via chat.
