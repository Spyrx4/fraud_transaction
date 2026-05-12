"""
model_loader.py - Memuat trained pipeline dan menjalankan prediksi.

Konsep: Singleton Pattern
=========================
Model ML berukuran besar (pipeline kita ~2.4MB). Kalau setiap request
harus load dari disk, akan sangat lambat.

Solusi: Load SEKALI saat server start, simpan di memori, pakai berkali-kali.
Inilah yang disebut "Singleton Pattern" — hanya ada 1 instance model
sepanjang hidup aplikasi.

  Server start → load model ke RAM → request 1 pakai → request 2 pakai → ...

Alur prediksi:
  1. Data mentah masuk (bisa kotor, ada NaN)
  2. pipeline.predict_proba() menjalankan semua step otomatis:
     Clean → Impute → Feature Eng → Scale → Classify
  3. Output: probability antara 0.0 - 1.0
     - 0.0 = pasti bukan fraud
     - 1.0 = pasti fraud
  4. Kita konversi ke risk level: LOW / MEDIUM / HIGH
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np

# Tambahkan path src agar bisa import class pipeline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Variable global untuk menyimpan model (singleton)
_pipeline = None

# Path ke file model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'fraud_pipeline.joblib')

# Nama kolom fitur yang diharapkan oleh model (sesuai training)
FEATURE_COLUMNS = [
    'age', 'transaction_amount', 'account_balance', 
    'num_transactions_today', 'is_foreign_transaction', 
    'transaction_hour', 'prev_fraud_flag',
    'merchant_distance_km', 'merchant_risk_score'
]


def load_model():
    """
    Load model dari file .joblib ke memori.
    
    Dipanggil sekali saat server start (di main.py startup event).
    Setelah ini, predict_fraud() bisa dipakai tanpa load ulang.
    
    Kenapa global variable?
    Karena FastAPI menjalankan setiap request di thread/event berbeda.
    Global variable bisa diakses dari semua request handlers.
    Di production yang lebih besar, biasanya pakai dependency injection.
    """
    global _pipeline
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run 'python train_and_save.py' first!"
        )
    
    _pipeline = joblib.load(MODEL_PATH)
    print(f"Model loaded from: {MODEL_PATH}")
    print(f"Pipeline steps: {[step[0] for step in _pipeline.steps]}")


def predict_fraud(data: dict) -> dict:
    """
    Menjalankan prediksi fraud pada 1 transaksi.
    
    Parameters:
        data: dict dengan key sesuai FEATURE_COLUMNS
              Contoh: {'age': 35, 'transaction_amount': 500.0, ...}
    
    Returns:
        dict berisi:
        - fraud_probability: float (0.0 - 1.0)
        - risk_level: "LOW" / "MEDIUM" / "HIGH"
        - prediction: 0 atau 1
    
    Konsep predict_proba vs predict:
    - predict()       → output: 0 atau 1 (binary)
    - predict_proba() → output: [prob_class_0, prob_class_1]
      
    Kita pakai predict_proba karena:
    1. Lebih informatif (87% fraud vs "fraud")
    2. Bisa set threshold sendiri (tidak harus 50%)
    3. Dashboard bisa menampilkan gauge/meter
    """
    if _pipeline is None:
        raise RuntimeError("Model belum di-load! Panggil load_model() dulu.")
    
    # Konversi dict ke DataFrame (karena pipeline mengharapkan DataFrame)
    # DataFrame 1 baris = 1 transaksi
    df = pd.DataFrame([data], columns=FEATURE_COLUMNS)
    
    # predict_proba mengembalikan array [[prob_normal, prob_fraud]]
    # Kita ambil prob_fraud (index 1)
    probabilities = _pipeline.predict_proba(df)
    fraud_prob = float(probabilities[0][1])
    
    # Tentukan risk level berdasarkan threshold
    if fraud_prob >= 0.8:
        risk_level = "HIGH"
    elif fraud_prob >= 0.5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Prediksi binary (0/1) berdasarkan threshold 0.5
    prediction = 1 if fraud_prob >= 0.5 else 0
    
    return {
        'fraud_probability': round(fraud_prob, 4),
        'risk_level': risk_level,
        'prediction': prediction
    }
