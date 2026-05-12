"""
train_and_save.py - Script untuk melatih dan menyimpan model fraud detection.

Konsep Production ML:
=====================
Di production, proses training dan serving DIPISAH:
1. Training (script ini)  → menghasilkan file model (.joblib)
2. Serving (FastAPI nanti) → memuat file model dan menerima request prediksi

Kenapa dipisah?
- Training butuh waktu lama & resource besar
- Serving harus cepat (< 100ms per request)
- Model bisa di-retrain tanpa menghentikan server

Cara pakai:
  cd ml-service
  python train_and_save.py
"""

import sys
import os

# ============================================================
# PENTING: Menambahkan path 'src' agar Python bisa menemukan
# modul fraud_training_pipeline dan feature_engineer.
# Di production biasanya ini dihandle oleh package management
# (setup.py / pyproject.toml), tapi untuk belajar ini cukup.
# ============================================================
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score, make_scorer
from xgboost import XGBClassifier
from fraud_training_pipeline import build_fraud_pipeline, FraudDataCleaner, XGBPredictiveImputer
from feature_engineer import FraudFeatureEngineer

def main():
    # ============================================================
    # STEP 1: Load Data
    # ============================================================
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'credit_fraud.csv')
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts()}\n")

    # ============================================================
    # STEP 2: Pisahkan Features (X) dan Target (y)
    # ============================================================
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']

    # ============================================================
    # STEP 3: Split Data
    # ============================================================
    # Kenapa 3 set (train/val/test)?
    # - Train (60%): Untuk melatih model
    # - Validation (20%): Untuk tuning hyperparameter
    # - Test (20%): Evaluasi FINAL — hanya disentuh sekali
    #
    # stratify=y memastikan rasio fraud/normal sama di setiap set.
    # ============================================================
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    print(f"Data split: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")

    # ============================================================
    # STEP 4: Preprocessing (Clean → Impute → Feature Eng)
    # ============================================================
    # Kenapa preprocessing DIPISAH dari tuning?
    #
    # Pipeline kita punya XGBPredictiveImputer yang MAHAL:
    # - Setiap fit() melatih XGBoost model per kolom yang punya NaN
    # - Jika digabung di RandomizedSearchCV (5 fold x 30 kombinasi),
    #   imputer akan di-retrain 150x → sangat lambat!
    #
    # Solusi: Jalankan preprocessing SEKALI di luar tuning.
    # Ini aman karena kita hanya tune classifier, bukan preprocessor.
    #
    # PENTING: Preprocessing di-fit pada training data SAJA.
    # Val & Test hanya di-transform (bukan fit) → mencegah data leakage.
    # ============================================================
    print("\nStep 1: Preprocessing data (Clean + Impute + Feature Engineering)...")
    
    preprocess_pipeline = Pipeline([
        ('cleaner', FraudDataCleaner()),
        ('imputer', XGBPredictiveImputer()),
        ('feature_eng', FraudFeatureEngineer()),
    ])
    
    # fit_transform pada train: belajar dari data training
    X_train_processed = preprocess_pipeline.fit_transform(X_train)
    # transform pada val & test: pakai apa yang dipelajari dari train
    X_val_processed = preprocess_pipeline.transform(X_val)
    X_test_processed = preprocess_pipeline.transform(X_test)
    
    print(f"  Features after engineering: {X_train_processed.shape[1]} columns")
    print(f"  Columns: {list(X_train_processed.columns)}")

    # ============================================================
    # STEP 5: Hyperparameter Tuning (RandomizedSearchCV)
    # ============================================================
    # Konsep Hyperparameter Tuning:
    # ==============================
    # Hyperparameter = pengaturan model yang TIDAK dipelajari dari data,
    # tapi ditentukan oleh kita sebelum training.
    #
    # Contoh hyperparameter XGBoost:
    # - n_estimators  : Jumlah tree (lebih banyak = lebih kompleks)
    # - max_depth     : Kedalaman tree (lebih dalam = lebih detail)
    # - learning_rate : Seberapa cepat model belajar
    # - subsample     : Fraksi data yang dipakai per tree
    # - colsample_bytree : Fraksi fitur yang dipakai per tree
    #
    # RandomizedSearchCV vs GridSearchCV:
    # - Grid: mencoba SEMUA kombinasi (lambat, exhaustive)
    # - Randomized: mencoba N RANDOM kombinasi (cepat, efisien)
    #
    #   Contoh: 5 params x 5 values = 3125 kombinasi (Grid)
    #           vs 30 random samples (Randomized)
    #   Research menunjukkan Randomized sering menemukan hasil
    #   yang hampir sama baiknya dengan 1/100 waktu.
    #
    # Cross-Validation (cv=5):
    # Data training dibagi 5 bagian. Setiap kombinasi parameter
    # diuji 5 kali (tiap bagian jadi "val" bergantian).
    # Ini memberikan estimasi performa yang lebih stabil.
    # ============================================================
    print("\nStep 2: Hyperparameter Tuning (RandomizedSearchCV)...")
    print("  Ini mungkin memakan waktu 1-3 menit...\n")

    # Parameter search space
    param_distributions = {
        'classifier__n_estimators': [50, 100, 200, 300, 500],
        'classifier__max_depth': [3, 4, 5, 6, 7, 8, 10],
        'classifier__learning_rate': [0.01, 0.05, 0.1, 0.2, 0.3],
        'classifier__subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'classifier__colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'classifier__min_child_weight': [1, 3, 5, 7],
        'classifier__gamma': [0, 0.1, 0.2, 0.3, 0.5],
        'classifier__reg_alpha': [0, 0.01, 0.1, 1.0],
        'classifier__reg_lambda': [0.5, 1.0, 2.0, 5.0],
    }
    # Total kemungkinan kombinasi: 5×7×5×5×5×4×5×4×4 = 1,750,000
    # Kita hanya coba 30 random → sangat efisien!

    # Pipeline mini: Scaler + Classifier (preprocessing sudah dilakukan)
    tuning_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', XGBClassifier(
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42
        ))
    ])

    # Scoring: F1-score pada kelas fraud (kelas 1)
    # Kenapa F1 bukan Accuracy?
    # - Accuracy bisa menyesatkan pada data imbalanced
    #   (Model yang selalu bilang "normal" bisa 90% akurat
    #    jika hanya 10% data yang fraud)
    # - F1 = harmonic mean dari Precision dan Recall
    #   → model harus bagus di KEDUA metrik
    f1_fraud_scorer = make_scorer(f1_score, pos_label=1)

    search = RandomizedSearchCV(
        tuning_pipeline,
        param_distributions=param_distributions,
        n_iter=30,           # Coba 30 kombinasi random
        cv=5,                # 5-fold cross validation
        scoring=f1_fraud_scorer,
        random_state=42,
        n_jobs=-1,           # Pakai semua CPU cores (paralel)
        verbose=1,           # Print progress
        return_train_score=True  # Simpan train score juga (untuk cek overfitting)
    )

    search.fit(X_train_processed, y_train)

    # ============================================================
    # STEP 5b: Analisis Hasil Tuning
    # ============================================================
    print("\n" + "=" * 60)
    print("HYPERPARAMETER TUNING RESULTS")
    print("=" * 60)
    
    print(f"\nBest F1-Score (CV): {search.best_score_:.4f}")
    print(f"\nBest Parameters:")
    for param, value in search.best_params_.items():
        # Hapus prefix 'classifier__' agar lebih mudah dibaca
        clean_name = param.replace('classifier__', '')
        print(f"  {clean_name}: {value}")

    # Cek overfitting: bandingkan train score vs CV score
    best_idx = search.best_index_
    train_score = search.cv_results_['mean_train_score'][best_idx]
    cv_score = search.cv_results_['mean_test_score'][best_idx]
    gap = train_score - cv_score
    print(f"\n  Train F1: {train_score:.4f}")
    print(f"  CV F1:    {cv_score:.4f}")
    print(f"  Gap:      {gap:.4f}", end="")
    if gap > 0.1:
        print(" [WARNING: kemungkinan overfitting!]")
    elif gap > 0.05:
        print(" [OK: sedikit overfitting, masih wajar]")
    else:
        print(" [GOOD: generalisasi baik]")

    # ============================================================
    # STEP 6: Build Final Pipeline dengan Best Params
    # ============================================================
    # Sekarang kita gabungkan kembali preprocessing + best classifier
    # menjadi 1 pipeline utuh, lalu retrain pada train+val data.
    #
    # Kenapa retrain pada train+val?
    # Karena tuning sudah selesai, kita tidak perlu val set lagi.
    # Lebih banyak data training = model lebih baik.
    # Test set tetap TIDAK TERSENTUH sampai evaluasi final.
    # ============================================================
    print("\nStep 3: Building final pipeline with best parameters...")
    
    best_classifier_params = {
        k.replace('classifier__', ''): v 
        for k, v in search.best_params_.items()
    }
    best_classifier_params['use_label_encoder'] = False
    best_classifier_params['eval_metric'] = 'logloss'
    best_classifier_params['random_state'] = 42

    final_pipeline = Pipeline([
        ('cleaner', FraudDataCleaner()),
        ('imputer', XGBPredictiveImputer()),
        ('feature_eng', FraudFeatureEngineer()),
        ('scaler', StandardScaler()),
        ('classifier', XGBClassifier(**best_classifier_params))
    ])

    # Retrain pada train + val (lebih banyak data)
    X_train_full_combined = pd.concat([X_train, X_val])
    y_train_full_combined = pd.concat([y_train, y_val])
    
    print(f"  Retraining on combined Train+Val: {X_train_full_combined.shape[0]} samples")
    final_pipeline.fit(X_train_full_combined, y_train_full_combined)
    print("  Training complete!")

    # ============================================================
    # STEP 7: Final Evaluation on Test Set
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST SET RESULTS (Final Evaluation - Tuned Model)")
    print("=" * 60)
    y_test_pred = final_pipeline.predict(X_test)
    print(classification_report(y_test, y_test_pred, target_names=['Normal', 'Fraud']))

    f1 = f1_score(y_test, y_test_pred)
    print(f"Test F1-Score (Fraud class): {f1:.4f}")

    # Bandingkan dengan baseline (default params)
    print("\n--- Perbandingan dengan Default Parameters ---")
    baseline_pipeline = build_fraud_pipeline()
    baseline_pipeline.fit(X_train_full_combined, y_train_full_combined)
    y_baseline_pred = baseline_pipeline.predict(X_test)
    f1_baseline = f1_score(y_test, y_baseline_pred)
    print(f"  Baseline F1 (default params): {f1_baseline:.4f}")
    print(f"  Tuned F1 (best params):       {f1:.4f}")
    improvement = ((f1 - f1_baseline) / f1_baseline) * 100
    print(f"  Improvement:                  {improvement:+.2f}%")

    # ============================================================
    # STEP 8: Save Model
    # ============================================================
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, 'fraud_pipeline.joblib')
    joblib.dump(final_pipeline, model_path)
    print(f"\nModel saved to: {model_path}")
    print(f"File size: {os.path.getsize(model_path) / 1024:.1f} KB")

    # Simpan juga best params untuk referensi
    params_path = os.path.join(model_dir, 'best_params.txt')
    with open(params_path, 'w') as f:
        f.write("Best Hyperparameters (from RandomizedSearchCV)\n")
        f.write(f"CV F1-Score: {search.best_score_:.4f}\n")
        f.write(f"Test F1-Score: {f1:.4f}\n\n")
        for param, value in best_classifier_params.items():
            f.write(f"{param}: {value}\n")
    print(f"Best params saved to: {params_path}")

    # ============================================================
    # STEP 9: Verifikasi
    # ============================================================
    print("\nVerifying saved model...")
    loaded_pipeline = joblib.load(model_path)
    y_verify = loaded_pipeline.predict(X_test)

    if (y_verify == y_test_pred).all():
        print("[PASSED] Verification OK - Saved model produces identical predictions")
    else:
        print("[FAILED] Verification ERROR - Predictions differ!")

if __name__ == '__main__':
    main()
