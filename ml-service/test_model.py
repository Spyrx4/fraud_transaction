"""
test_model.py - Script untuk menguji model fraud detection yang sudah di-train.

Konsep Testing di ML Production:
=================================
Sebelum model di-deploy ke production (FastAPI), kita perlu memastikan:
1. Model bisa di-load tanpa error
2. Input valid menghasilkan output yang benar formatnya
3. Input edge-case (batas atas/bawah) tidak crash
4. Prediksi masuk akal (transaksi mencurigakan → fraud tinggi)
5. Performa model memenuhi threshold minimum

Cara pakai:
  cd ml-service
  py test_model.py

Atau gunakan pytest (jika ingin integrasi CI/CD):
  py -m pytest test_model.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    classification_report, f1_score, precision_score,
    recall_score, accuracy_score, confusion_matrix, roc_auc_score
)
from sklearn.model_selection import train_test_split

# ============================================================
# Konfigurasi
# ============================================================
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'fraud_pipeline.joblib')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'credit_fraud.csv')

# Threshold minimum performa yang bisa diterima untuk production
# Jika di bawah ini, model TIDAK BOLEH di-deploy
MIN_F1_SCORE = 0.65
MIN_RECALL_FRAUD = 0.60     # Recall fraud harus >= 60% (jangan sampai banyak fraud lolos)
MIN_PRECISION_FRAUD = 0.60  # Precision harus >= 60% (jangan terlalu banyak false alarm)

PASSED = 0
FAILED = 0


def log_result(test_name: str, passed: bool, detail: str = ""):
    """Helper untuk print hasil test."""
    global PASSED, FAILED
    status = "[PASS]" if passed else "[FAIL]"
    if passed:
        PASSED += 1
    else:
        FAILED += 1
    print(f"  {status} {test_name}")
    if detail:
        print(f"         {detail}")


# ============================================================
# TEST 1: Model Loading
# ============================================================
def test_model_loading():
    """
    Pastikan file model ada dan bisa di-load.
    Jika file corrupt atau versi library tidak cocok, ini akan gagal.
    """
    print("\n[TEST 1] Model Loading")
    print("-" * 50)

    # 1a. File exists
    exists = os.path.exists(MODEL_PATH)
    log_result("Model file exists", exists, MODEL_PATH)

    # 1b. File bisa di-load
    try:
        pipeline = joblib.load(MODEL_PATH)
        log_result("Model loads without error", True)
    except Exception as e:
        log_result("Model loads without error", False, str(e))
        return None

    # 1c. Pipeline punya step yang benar
    expected_steps = ['cleaner', 'imputer', 'feature_eng', 'scaler', 'classifier']
    actual_steps = [name for name, _ in pipeline.steps]
    match = actual_steps == expected_steps
    log_result("Pipeline steps correct", match,
               f"Expected: {expected_steps}, Got: {actual_steps}")

    # 1d. File size reasonable (bukan 0 bytes, bukan terlalu besar)
    size_kb = os.path.getsize(MODEL_PATH) / 1024
    reasonable = 100 < size_kb < 50000  # antara 100KB dan 50MB
    log_result("File size reasonable", reasonable, f"{size_kb:.1f} KB")

    return pipeline


# ============================================================
# TEST 2: Prediction Format & Output
# ============================================================
def test_prediction_format(pipeline):
    """
    Pastikan output prediksi memiliki format yang benar.
    Ini penting karena FastAPI endpoint bergantung pada format ini.
    """
    print("\n[TEST 2] Prediction Format & Output")
    print("-" * 50)

    # Sample data - 1 transaksi normal
    sample = pd.DataFrame([{
        'age': 35, 'transaction_amount': 200, 'account_balance': 15000,
        'num_transactions_today': 2, 'is_foreign_transaction': 0,
        'transaction_hour': 14, 'prev_fraud_flag': 0,
        'merchant_distance_km': 5, 'merchant_risk_score': 2.0
    }])

    # 2a. predict() menghasilkan array
    try:
        pred = pipeline.predict(sample)
        is_array = isinstance(pred, np.ndarray)
        log_result("predict() returns ndarray", is_array, f"Type: {type(pred).__name__}")
    except Exception as e:
        log_result("predict() returns ndarray", False, str(e))
        return

    # 2b. predict() menghasilkan 0 atau 1
    valid_classes = pred[0] in [0, 1]
    log_result("predict() returns 0 or 1", valid_classes, f"Value: {pred[0]}")

    # 2c. predict_proba() menghasilkan probabilitas
    try:
        proba = pipeline.predict_proba(sample)
        has_two_cols = proba.shape[1] == 2
        log_result("predict_proba() returns 2 classes", has_two_cols, f"Shape: {proba.shape}")
    except Exception as e:
        log_result("predict_proba() returns 2 classes", False, str(e))
        return

    # 2d. Probabilitas antara 0 dan 1
    in_range = (proba >= 0).all() and (proba <= 1).all()
    log_result("Probabilities in [0, 1] range", in_range,
               f"Normal: {proba[0][0]:.4f}, Fraud: {proba[0][1]:.4f}")

    # 2e. Probabilitas menjumlah ke 1
    sums_to_one = abs(proba[0].sum() - 1.0) < 1e-6
    log_result("Probabilities sum to 1", sums_to_one, f"Sum: {proba[0].sum():.6f}")


# ============================================================
# TEST 3: Sanity Check (Apakah prediksi masuk akal?)
# ============================================================
def test_sanity_check(pipeline):
    """
    Test apakah model memberikan prediksi yang masuk akal.
    Transaksi yang jelas mencurigakan harus punya fraud score tinggi,
    dan transaksi normal harus rendah.
    """
    print("\n[TEST 3] Sanity Check (Prediksi Masuk Akal)")
    print("-" * 50)

    # Transaksi sangat mencurigakan
    suspicious = pd.DataFrame([{
        'age': 22,
        'transaction_amount': 9999,         # Jumlah sangat besar
        'account_balance': 500,             # Saldo sangat kecil
        'num_transactions_today': 15,       # Transaksi sangat banyak hari ini
        'is_foreign_transaction': 1,        # Luar negeri
        'transaction_hour': 3,              # Jam 3 pagi
        'prev_fraud_flag': 1,               # Pernah fraud sebelumnya
        'merchant_distance_km': 800,        # Lokasi sangat jauh
        'merchant_risk_score': 9.5          # Merchant risiko tinggi
    }])

    # Transaksi sangat normal
    normal = pd.DataFrame([{
        'age': 45,
        'transaction_amount': 50,           # Jumlah kecil
        'account_balance': 50000,           # Saldo besar
        'num_transactions_today': 1,        # Transaksi pertama hari ini
        'is_foreign_transaction': 0,        # Domestik
        'transaction_hour': 12,             # Siang hari
        'prev_fraud_flag': 0,               # Tidak pernah fraud
        'merchant_distance_km': 2,          # Dekat rumah
        'merchant_risk_score': 0.5          # Merchant aman
    }])

    prob_suspicious = pipeline.predict_proba(suspicious)[0][1]
    prob_normal = pipeline.predict_proba(normal)[0][1]

    # 3a. Transaksi mencurigakan harus punya fraud score > 0.7
    log_result("Suspicious transaction -> high fraud score",
               prob_suspicious > 0.7,
               f"Score: {prob_suspicious:.4f} (expected > 0.7)")

    # 3b. Transaksi normal harus punya fraud score < 0.3
    log_result("Normal transaction -> low fraud score",
               prob_normal < 0.3,
               f"Score: {prob_normal:.4f} (expected < 0.3)")

    # 3c. Suspicious harus lebih tinggi dari normal
    log_result("Suspicious > Normal score",
               prob_suspicious > prob_normal,
               f"Suspicious: {prob_suspicious:.4f} vs Normal: {prob_normal:.4f}")


# ============================================================
# TEST 4: Edge Cases (Kondisi Batas)
# ============================================================
def test_edge_cases(pipeline):
    """
    Test apakah model bisa handle input di batas valid.
    Di production, user bisa mengirim input apapun.
    """
    print("\n[TEST 4] Edge Cases (Kondisi Batas)")
    print("-" * 50)

    edge_cases = [
        ("Minimum values (semua 0)", {
            'age': 0, 'transaction_amount': 0, 'account_balance': 0,
            'num_transactions_today': 0, 'is_foreign_transaction': 0,
            'transaction_hour': 0, 'prev_fraud_flag': 0,
            'merchant_distance_km': 0, 'merchant_risk_score': 0
        }),
        ("Maximum realistic values", {
            'age': 100, 'transaction_amount': 999999, 'account_balance': 999999,
            'num_transactions_today': 50, 'is_foreign_transaction': 1,
            'transaction_hour': 23, 'prev_fraud_flag': 1,
            'merchant_distance_km': 10000, 'merchant_risk_score': 10
        }),
        ("Very young user", {
            'age': 18, 'transaction_amount': 100, 'account_balance': 500,
            'num_transactions_today': 1, 'is_foreign_transaction': 0,
            'transaction_hour': 10, 'prev_fraud_flag': 0,
            'merchant_distance_km': 1, 'merchant_risk_score': 1
        }),
        ("Very old user", {
            'age': 90, 'transaction_amount': 100, 'account_balance': 50000,
            'num_transactions_today': 1, 'is_foreign_transaction': 0,
            'transaction_hour': 9, 'prev_fraud_flag': 0,
            'merchant_distance_km': 1, 'merchant_risk_score': 1
        }),
    ]

    for name, data in edge_cases:
        df = pd.DataFrame([data])
        try:
            proba = pipeline.predict_proba(df)[0][1]
            valid = 0 <= proba <= 1
            log_result(name, valid, f"Fraud prob: {proba:.4f}")
        except Exception as e:
            log_result(name, False, f"ERROR: {e}")


# ============================================================
# TEST 5: Batch Prediction (Multiple rows)
# ============================================================
def test_batch_prediction(pipeline):
    """
    Test apakah model bisa handle banyak data sekaligus.
    Di production, mungkin ada batch processing.
    """
    print("\n[TEST 5] Batch Prediction")
    print("-" * 50)

    # 100 transaksi random
    np.random.seed(42)
    batch = pd.DataFrame({
        'age': np.random.uniform(18, 80, 100),
        'transaction_amount': np.random.uniform(10, 10000, 100),
        'account_balance': np.random.uniform(0, 100000, 100),
        'num_transactions_today': np.random.randint(0, 20, 100),
        'is_foreign_transaction': np.random.randint(0, 2, 100),
        'transaction_hour': np.random.randint(0, 24, 100),
        'prev_fraud_flag': np.random.randint(0, 2, 100),
        'merchant_distance_km': np.random.uniform(0, 1000, 100),
        'merchant_risk_score': np.random.uniform(0, 10, 100),
    })

    try:
        preds = pipeline.predict(batch)
        probas = pipeline.predict_proba(batch)

        log_result("Batch predict (100 rows) succeeds", True, f"Output shape: {preds.shape}")

        # Semua prediksi harus 0 atau 1
        valid_preds = set(preds).issubset({0, 1})
        log_result("All predictions are 0 or 1", valid_preds, f"Unique: {set(preds)}")

        # Ada variasi (bukan semua sama)
        has_variety = len(set(preds)) > 1
        log_result("Predictions have variety (not all same)", has_variety,
                   f"Fraud: {sum(preds==1)}, Normal: {sum(preds==0)}")

    except Exception as e:
        log_result("Batch predict (100 rows) succeeds", False, str(e))


# ============================================================
# TEST 6: Performance on Test Set (Metrik Utama)
# ============================================================
def test_performance(pipeline):
    """
    Evaluasi performa model pada data test asli.
    Ini adalah TEST PALING PENTING — apakah model cukup bagus
    untuk digunakan di production?
    """
    print("\n[TEST 6] Performance on Test Set")
    print("-" * 50)

    # Load dan split data seperti saat training
    df = pd.read_csv(DATA_PATH)
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Prediksi
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    # Hitung metrik
    f1 = f1_score(y_test, y_pred, pos_label=1)
    precision = precision_score(y_test, y_pred, pos_label=1)
    recall = recall_score(y_test, y_pred, pos_label=1)
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print(f"\n  Accuracy:        {accuracy:.4f}")
    print(f"  F1-Score (Fraud): {f1:.4f}")
    print(f"  Precision:       {precision:.4f}")
    print(f"  Recall:          {recall:.4f}")
    print(f"  AUC-ROC:         {auc:.4f}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"\n  Confusion Matrix:")
    print(f"                    Predicted Normal  Predicted Fraud")
    print(f"  Actual Normal     {tn:>15}  {fp:>15}")
    print(f"  Actual Fraud      {fn:>15}  {tp:>15}")
    print(f"\n  True Negatives:   {tn} (Normal terdeteksi benar)")
    print(f"  False Positives:  {fp} (Normal salah ditandai fraud)")
    print(f"  False Negatives:  {fn} (Fraud lolos tidak terdeteksi!)")
    print(f"  True Positives:   {tp} (Fraud berhasil ditangkap)")

    # Classification Report
    print(f"\n  Full Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Fraud']))

    # Threshold checks
    log_result(f"F1-Score >= {MIN_F1_SCORE}", f1 >= MIN_F1_SCORE,
               f"F1: {f1:.4f} (threshold: {MIN_F1_SCORE})")
    log_result(f"Recall >= {MIN_RECALL_FRAUD}", recall >= MIN_RECALL_FRAUD,
               f"Recall: {recall:.4f} (threshold: {MIN_RECALL_FRAUD})")
    log_result(f"Precision >= {MIN_PRECISION_FRAUD}", precision >= MIN_PRECISION_FRAUD,
               f"Precision: {precision:.4f} (threshold: {MIN_PRECISION_FRAUD})")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  FRAUD DETECTION MODEL TEST SUITE")
    print("=" * 60)

    # Test 1: Load
    pipeline = test_model_loading()
    if pipeline is None:
        print("\n[ABORT] Model gagal di-load. Test selanjutnya dibatalkan.")
        sys.exit(1)

    # Test 2-6: Functional & Performance
    test_prediction_format(pipeline)
    test_sanity_check(pipeline)
    test_edge_cases(pipeline)
    test_batch_prediction(pipeline)
    test_performance(pipeline)

    # Summary
    total = PASSED + FAILED
    print("\n" + "=" * 60)
    print(f"  TEST SUMMARY: {PASSED}/{total} passed, {FAILED}/{total} failed")
    print("=" * 60)

    if FAILED == 0:
        print("  All tests passed! Model is ready for production deployment.")
    else:
        print("  Some tests failed. Review the issues above before deploying.")

    sys.exit(0 if FAILED == 0 else 1)
