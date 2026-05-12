# Penjelasan Fitur Data Fraud Detection

Dokumen ini memberikan penjelasan mengenai setiap fitur (kolom) yang terdapat dalam dataset deteksi penipuan (`credit_fraud.csv`) untuk membantu memahami konteks permasalahan.

## Daftar Fitur

| Nama Fitur | Deskripsi | Tipe Data |
| :--- | :--- | :--- |
| **age** | Usia pemilik akun/kartu. | Numerik (Float/Integer) |
| **transaction_amount** | Jumlah nominal transaksi yang dilakukan. | Numerik (Float) |
| **account_balance** | Saldo terakhir yang tersedia di akun sebelum transaksi. | Numerik (Float) |
| **num_transactions_today** | Jumlah total transaksi yang telah dilakukan hari ini oleh akun tersebut. | Numerik (Integer) |
| **is_foreign_transaction** | Indikator apakah transaksi dilakukan di luar negeri atau menggunakan mata uang asing (0 = Tidak, 1 = Ya). | Kategorikal (Binary) |
| **transaction_hour** | Waktu (jam) saat transaksi terjadi dalam format 24 jam (0-23). | Numerik/Ordinal |
| **prev_fraud_flag** | Indikator apakah akun ini pernah terkait dengan aktivitas mencurigakan atau fraud sebelumnya (0 = Tidak, 1 = Ya). | Kategorikal (Binary) |
| **merchant_distance_km** | Jarak geografis antara lokasi transaksi (merchant) dengan lokasi rumah atau lokasi biasa pengguna. | Numerik (Float) |
| **merchant_risk_score** | Skor risiko yang diberikan kepada merchant berdasarkan histori transaksi sebelumnya (biasanya skala 0-10). | Numerik (Float) |
| **is_fraud** | **Target Variable**: Label yang menunjukkan apakah transaksi ini adalah penipuan (0 = Normal, 1 = Fraud). | Kategorikal (Binary) |

## Konteks Permasalahan & Kualitas Data

Berdasarkan analisis awal pada dataset, terdapat beberapa hal penting yang perlu diperhatikan:

1.  **Data Kotor (Dirty Data):** Terdapat nilai-nilai anomali yang perlu ditangani sebelum pemodelan, seperti:
    *   Usia negatif (misal: `-10.0`).
    *   Format string pada kolom numerik (misal: `37.0_err`).
    *   Nilai saldo yang tidak realistis (misal: `-99999.0` sebagai placeholder error).
    *   Waktu transaksi di luar jam normal (misal: `28.0` jam).
2.  **Missing Values:** Beberapa kolom memiliki data kosong (NaN) yang memerlukan teknik imputasi (seperti penggunaan XGBoost Imputer yang sedang Anda evaluasi).
3.  **Tujuan Utama:** Model diharapkan dapat memprediksi `is_fraud` secara akurat dengan mempertimbangkan pola-pola dari fitur pendukung seperti `transaction_amount`, `merchant_risk_score`, dan `merchant_distance_km` yang sering kali menjadi indikator kuat terjadinya fraud.
