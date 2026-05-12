"""
database.py - Setup dan operasi database PostgreSQL untuk menyimpan transaksi.

Konsep: SQLite vs PostgreSQL
=============================
Kita migrasi dari SQLite ke PostgreSQL. Berikut perbedaan penting:

| Aspek              | SQLite                      | PostgreSQL                     |
|--------------------|-----------------------------|---------------------------------|
| Arsitektur         | File-based (1 file .db)     | Client-Server (daemon process)  |
| Concurrency        | 1 writer pada satu waktu    | Banyak writer bersamaan (MVCC)  |
| Koneksi            | sqlite3.connect(file_path)  | psycopg2.connect(host, port...) |
| Placeholder        | ? (question mark)           | %s (percent-s)                  |
| Auto-increment     | AUTOINCREMENT               | SERIAL                          |
| Tipe REAL          | REAL                        | DOUBLE PRECISION                |
| Production-ready   | Tidak (demo/embedded)       | Ya (standar industri)           |

Konsep: Environment Variables (.env)
=====================================
Credentials database (host, password, dll) TIDAK BOLEH di-hardcode dalam kode.
Kenapa?
1. Keamanan — Jika kode di-push ke GitHub, password ikut terbuka
2. Fleksibilitas — Beda environment (dev/staging/prod) beda credentials
3. Best Practice — 12-Factor App methodology

Kita gunakan file `.env` yang di-load oleh `python-dotenv`:
  DB_HOST=localhost
  DB_PORT=5433
  DB_NAME=fraud_detection
  DB_USER=postgres
  DB_PASSWORD=password_anda

File .env WAJIB masuk .gitignore!

Tabel `transactions`:
- id              : ID unik auto-increment (SERIAL di PostgreSQL)
- age, dll        : Data asli dari form nasabah
- fraud_probability : Hasil prediksi model (0.0 - 1.0)
- risk_level       : 'LOW' / 'MEDIUM' / 'HIGH'
- status           : 'pending' / 'approved' / 'rejected'
- created_at       : Waktu transaksi masuk (TIMESTAMP)
"""

import psycopg2
import psycopg2.extras  # Untuk RealDictCursor
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables dari file .env
# Ini mencari file .env di direktori saat ini atau parent
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Konfigurasi database dari environment variables
# os.getenv('KEY', 'default') → ambil dari .env, jika tidak ada pakai default
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'dbname': os.getenv('DB_NAME', 'fraud_detection'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
}


def get_connection():
    """
    Membuat koneksi ke PostgreSQL database.
    
    Perbedaan dari SQLite:
    - SQLite: sqlite3.connect('file.db')  → langsung ke file
    - PostgreSQL: psycopg2.connect(host=..., port=...) → ke server
    
    cursor_factory=RealDictCursor membuat hasil query langsung
    berupa dictionary: row['column_name'] bukan row[0].
    Di SQLite kita pakai row_factory, di PostgreSQL pakai cursor_factory.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def init_db():
    """
    Membuat tabel jika belum ada.
    
    Perbedaan SQL syntax dari SQLite:
    - SERIAL menggantikan INTEGER PRIMARY KEY AUTOINCREMENT
      (SERIAL = auto-increment integer di PostgreSQL)
    - DOUBLE PRECISION menggantikan REAL (lebih presisi)
    - TIMESTAMP menggantikan TEXT untuk waktu
      (PostgreSQL punya tipe TIMESTAMP native yang lebih powerful)
    - VARCHAR menggantikan TEXT untuk kolom dengan panjang terbatas
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            
            -- Data input dari nasabah (sesuai fitur dataset)
            age DOUBLE PRECISION,
            transaction_amount DOUBLE PRECISION,
            account_balance DOUBLE PRECISION,
            num_transactions_today INTEGER,
            is_foreign_transaction INTEGER,
            transaction_hour INTEGER,
            prev_fraud_flag INTEGER,
            merchant_distance_km DOUBLE PRECISION,
            merchant_risk_score DOUBLE PRECISION,
            
            -- Hasil prediksi model
            fraud_probability DOUBLE PRECISION,
            risk_level VARCHAR(10),
            
            -- Status keputusan bank
            status VARCHAR(10) DEFAULT 'pending',
            
            -- Timestamp (PostgreSQL native timestamp)
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print(f"Database initialized: {DB_CONFIG['dbname']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")


def insert_transaction(data: dict, fraud_probability: float, risk_level: str) -> int:
    """
    Simpan transaksi baru beserta hasil prediksi.
    
    Perbedaan dari SQLite:
    - Placeholder: %s bukan ?
      SQLite: VALUES (?, ?, ?)
      PostgreSQL: VALUES (%s, %s, %s)
    
    - RETURNING id: PostgreSQL bisa langsung return ID tanpa
      cursor.lastrowid. Ini lebih reliable dan atomic.
      SQLite tidak mendukung RETURNING clause.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO transactions 
        (age, transaction_amount, account_balance, num_transactions_today,
         is_foreign_transaction, transaction_hour, prev_fraud_flag,
         merchant_distance_km, merchant_risk_score,
         fraud_probability, risk_level, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
        RETURNING id
    ''', (
        data.get('age'),
        data.get('transaction_amount'),
        data.get('account_balance'),
        data.get('num_transactions_today'),
        data.get('is_foreign_transaction'),
        data.get('transaction_hour'),
        data.get('prev_fraud_flag'),
        data.get('merchant_distance_km'),
        data.get('merchant_risk_score'),
        fraud_probability,
        risk_level,
        datetime.now()
    ))
    transaction_id = cur.fetchone()[0]  # Ambil ID dari RETURNING
    conn.commit()
    cur.close()
    conn.close()
    return transaction_id


def get_transactions(status: str = None, limit: int = 100, offset: int = 0) -> list:
    """
    Ambil daftar transaksi dengan filter opsional.
    
    RealDictCursor membuat setiap row langsung jadi dict:
      {'id': 1, 'age': 35.0, 'status': 'pending', ...}
    
    Tanpa RealDictCursor, hasil query berupa tuple:
      (1, 35.0, 'pending', ...)
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if status:
        cur.execute(
            'SELECT * FROM transactions WHERE status = %s ORDER BY created_at DESC LIMIT %s OFFSET %s',
            (status, limit, offset)
        )
    else:
        cur.execute(
            'SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s OFFSET %s',
            (limit, offset)
        )
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Konversi datetime & Decimal ke tipe JSON-serializable
    result = []
    for row in rows:
        row_dict = dict(row)
        # PostgreSQL TIMESTAMP → string ISO format (agar bisa di-serialize ke JSON)
        if row_dict.get('created_at'):
            row_dict['created_at'] = row_dict['created_at'].isoformat()
        result.append(row_dict)
    
    return result


def update_transaction_status(transaction_id: int, new_status: str) -> bool:
    """
    Update status transaksi (pending -> approved/rejected).
    
    cursor.rowcount bekerja sama di SQLite dan PostgreSQL — 
    mengembalikan jumlah baris yang terpengaruh oleh query.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE transactions SET status = %s WHERE id = %s',
        (new_status, transaction_id)
    )
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    return affected > 0


def get_dashboard_stats() -> dict:
    """
    Menghitung statistik untuk dashboard.
    
    SQL aggregate functions (COUNT, AVG, SUM) bekerja sama
    di SQLite dan PostgreSQL. Yang beda hanya:
    - PostgreSQL punya COALESCE bawaan yang lebih robust
    - PostgreSQL bisa ROUND ke NUMERIC, bukan REAL
    
    COALESCE(value, 0) → jika value NULL, ganti jadi 0.
    Ini penting saat tabel kosong (belum ada transaksi).
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Stats utama
    cur.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            COALESCE(ROUND(AVG(fraud_probability)::numeric * 100, 1), 0) as avg_fraud_pct,
            COALESCE(SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END), 0) as total_approved,
            COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0) as total_rejected,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0) as total_pending,
            COALESCE(SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END), 0) as total_high_risk,
            COALESCE(SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END), 0) as total_medium_risk,
            COALESCE(SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END), 0) as total_low_risk
        FROM transactions
    ''')
    stats_row = cur.fetchone()
    
    # Konversi Decimal ke float untuk JSON serialization
    stats = {}
    for key, value in dict(stats_row).items():
        stats[key] = float(value) if value is not None else 0
    
    # Distribusi per jam (untuk chart)
    cur.execute('''
        SELECT transaction_hour as hour, 
               COUNT(*) as count,
               COALESCE(SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END), 0) as fraud_count
        FROM transactions 
        GROUP BY transaction_hour 
        ORDER BY transaction_hour
    ''')
    hourly_rows = cur.fetchall()
    stats['hourly_distribution'] = [dict(row) for row in hourly_rows]
    
    cur.close()
    conn.close()
    return stats


def bulk_update_by_risk(threshold_risk: float, condition: str, status: str) -> int:
    """
    Update status secara massal berdasarkan risk score.
    condition: '<' atau '>'
    """
    if condition not in ('<', '>'):
        raise ValueError("Condition must be '<' or '>'")
        
    conn = get_connection()
    cur = conn.cursor()
    
    query = f"UPDATE transactions SET status = %s WHERE fraud_probability {condition} %s AND status = 'pending'"
    cur.execute(query, (status, threshold_risk))
    
    conn.commit()
    affected = cur.rowcount
    cur.close()
    conn.close()
    return affected


def get_agent_summary() -> str:
    """
    Memberikan ringkasan database dalam bentuk teks untuk konteks AI Agent.
    """
    stats = get_dashboard_stats()
    return f"""
Kondisi Database Saat Ini:
- Total Transaksi: {stats.get('total_transactions', 0)}
- Transaksi Pending (Belum di-review): {stats.get('total_pending', 0)}
- Transaksi Disetujui (Approved): {stats.get('total_approved', 0)}
- Transaksi Ditolak (Rejected): {stats.get('total_rejected', 0)}
- Rata-rata Peluang Fraud: {stats.get('avg_fraud_pct', 0)}%
"""


def get_daily_report() -> dict:
    """
    Mengambil data laporan harian lengkap untuk dilampirkan oleh AI Agent.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Ambil transaksi 24 jam terakhir (PostgreSQL style timestamp handling)
    # Dalam implementasi ini kita asumsikan semua data hari ini
    # Atau bisa menggunakan DATE(created_at) = CURRENT_DATE
    cur.execute('''
        SELECT 
            COUNT(*) as total_today,
            COALESCE(SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END), 0) as high_risk_today,
            COALESCE(SUM(transaction_amount), 0) as total_volume_today,
            COALESCE(SUM(CASE WHEN risk_level = 'HIGH' THEN transaction_amount ELSE 0 END), 0) as high_risk_volume_today
        FROM transactions
        WHERE DATE(created_at) = CURRENT_DATE
    ''')
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        "total_transactions_today": float(row['total_today'] if row and row['total_today'] else 0),
        "high_risk_transactions": float(row['high_risk_today'] if row and row['high_risk_today'] else 0),
        "total_volume": float(row['total_volume_today'] if row and row['total_volume_today'] else 0),
        "high_risk_volume": float(row['high_risk_volume_today'] if row and row['high_risk_volume_today'] else 0)
    }
