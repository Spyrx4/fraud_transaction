import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score, recall_score, precision_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline

def clean_value_errors(df):
    """
    Membersihkan data kotor berdasarkan feature.md sebelum proses imputasi.
    Mengubah nilai error menjadi NaN agar bisa diisi oleh model.
    """
    df_clean = df.copy()
    
    # 1. Bersihkan akhiran '_err' di semua kolom dan konversi ke numeric
    for col in df_clean.columns:
        if df_clean[col].dtype == object:
            # Cari baris yang mengandung '_err'
            mask = df_clean[col].str.contains('_err', na=False)
            if mask.any():
                print(f"Cleaning: Menghapus format '_err' pada kolom {col}")
                # Hapus '_err'
                df_clean.loc[mask, col] = df_clean.loc[mask, col].str.replace('_err', '', regex=False)
        
        # Selalu coba konversi kolom yang relevan ke numeric sebelum pengecekan range
        if col in ['age', 'transaction_amount', 'account_balance', 'transaction_hour', 'num_transactions_today']:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    if 'age' in df_clean.columns:
        mask_age = df_clean['age'] < 0
        if mask_age.any():
            print(f"Cleaning: Mengubah {mask_age.sum()} baris usia negatif menjadi NaN")
            df_clean.loc[mask_age, 'age'] = np.nan

    if 'account_balance' in df_clean.columns:
        mask_bal = df_clean['account_balance'] == -99999.0
        if mask_bal.any():
            print(f"Cleaning: Mengubah {mask_bal.sum()} baris saldo placeholder menjadi NaN")
            df_clean.loc[mask_bal, 'account_balance'] = np.nan

    if 'transaction_hour' in df_clean.columns:
        mask_hour = (df_clean['transaction_hour'] < 0) | (df_clean['transaction_hour'] > 23)
        if mask_hour.any():
            print(f"Cleaning: Mengubah {mask_hour.sum()} baris jam tidak valid menjadi NaN")
            df_clean.loc[mask_hour, 'transaction_hour'] = np.nan

    return df_clean

def apply_imputation(df, configs):
    """
    Melakukan imputasi menggunakan model yang ditentukan (XGBoost atau RandomForest).
    """
    df_imputed = df.copy()
    
    for config in configs:
        target_col = config['target']
        pred_cols = config['pred_features']
        method = config.get('method', 'regressor')
        model_name = config.get('model_name', 'xgb')
        
        print(f"Imputing: {target_col} using {model_name} {method}...")
        
        # Ambil baris untuk training (di mana target tidak NaN)
        # XGBoost bisa menangani NaN pada pred_features
        train_data = df_imputed[df_imputed[target_col].notna()]
        
        if train_data.empty:
            print(f"Skipping {target_col}: No data available for training.")
            continue
            
        # Prediksi untuk baris di mana target NaN
        predict_mask = df_imputed[target_col].isna()
        
        if not predict_mask.any():
            print(f"No missing values to fill for {target_col}")
            continue
            
        X_train = train_data[pred_cols]
        y_train = train_data[target_col]
        X_predict = df_imputed.loc[predict_mask, pred_cols]
        
        # Model Selection
        if model_name == 'rf':
            if method == 'classifier':
                model = RandomForestClassifier(n_estimators=50, n_jobs=-1, random_state=42, class_weight='balanced')
            else:
                model = RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42)
        else: # Default: xgb
            if method == 'classifier':
                pos_count = (y_train == 1).sum()
                neg_count = (y_train == 0).sum()
                spw = neg_count / pos_count if pos_count > 0 else 1
                print(f"  - Class Distribution: Neg={neg_count}, Pos={pos_count} (SPW: {spw:.2f})")
                model = XGBClassifier(n_estimators=50, n_jobs=-1, random_state=42, eval_metric='logloss', scale_pos_weight=spw)
            else:
                model = XGBRegressor(n_estimators=50, n_jobs=-1, random_state=42)
            
        # Create Pipeline with Scaling
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])
        
        pipe.fit(X_train, y_train)
        predictions = pipe.predict(X_predict)
        
        # Rounding logic for binary/integer columns if using regressor
        if method == 'regressor':
            if target_col in ['is_foreign_transaction', 'prev_fraud_flag']:
                predictions = np.round(np.clip(predictions, 0, 1)).astype(int)
                print(f"  - Rounded predictions for binary feature {target_col}")
            elif target_col in ['num_transactions_today', 'transaction_hour', 'age']:
                predictions = np.round(predictions).astype(int)
                print(f"  - Rounded predictions for integer feature {target_col}")
            
        df_imputed.loc[predict_mask, target_col] = predictions
        print(f"Filled {predict_mask.sum()} missing values in {target_col}")

    return df_imputed

def evaluate_imputation(df, configs):
    """
    Evaluasi performa imputasi dengan berbagai model.
    """
    results = []
    print(f"\n{'Target Feature':<25} | {'Model':<6} | {'Type':<10} | {'Metrics (Focus on Minority Class 1)':<50}")
    print("-" * 110)

    for config in configs:
        target_col = config['target']
        pred_cols = config['pred_features']
        method = config.get('method', 'regressor')
        model_name = config.get('model_name', 'xgb')
        
        # Untuk evaluasi, kita butuh target yang valid
        data_subset = df[df[target_col].notna()].copy()
        
        if data_subset.empty: continue

        X = data_subset[pred_cols]
        y = data_subset[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Model Selection for Evaluation
        if model_name == 'rf':
            if method == 'classifier':
                model = RandomForestClassifier(n_estimators=50, n_jobs=-1, random_state=42, class_weight='balanced')
            else:
                model = RandomForestRegressor(n_estimators=50, n_jobs=-1, random_state=42)
        else: # xgb
            if method == 'classifier':
                pos_count = (y_train == 1).sum()
                neg_count = (y_train == 0).sum()
                spw = neg_count / pos_count if pos_count > 0 else 1
                model = XGBClassifier(n_estimators=50, n_jobs=-1, random_state=42, eval_metric='logloss', scale_pos_weight=spw)
            else:
                model = XGBRegressor(n_estimators=50, n_jobs=-1, random_state=42)

        # Create Pipeline with Scaling for Evaluation
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])

        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)

        if method == 'classifier':
            acc = accuracy_score(y_test, preds)
            f1_macro = f1_score(y_test, preds, average='macro')
            prec_1 = precision_score(y_test, preds, pos_label=1, zero_division=0)
            rec_1 = recall_score(y_test, preds, pos_label=1, zero_division=0)
            f1_1 = f1_score(y_test, preds, pos_label=1, zero_division=0)
            res_str = f"Acc: {acc:.3f} | Macro-F1: {f1_macro:.3f} | Class1(P/R/F1): {prec_1:.3f}/{rec_1:.3f}/{f1_1:.3f}"
        else:
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            mae = mean_absolute_error(y_test, preds)
            r2 = r2_score(y_test, preds)
            res_str = f"R2: {r2:.4f} | RMSE: {rmse:.2f} | MAE: {mae:.2f}"

        print(f"{target_col:<25} | {model_name:<10} | {method:<10} | {res_str}")
        results.append({'target': target_col, 'model': model_name, 'type': method, 'metrics': res_str})

    return results

def get_all_imputation_configs(df, target_to_exclude='is_fraud'):
    """
    Menggabungkan konfigurasi imputasi:
    1. Regresi untuk semua fitur dengan missing value (XGB).
    2. Klasifikasi khusus untuk fitur biner/kategorikal (XGB, RF).
    """
    cols_with_nans = df.columns[df.isnull().any()].tolist()
    features_to_impute = [col for col in cols_with_nans if col != target_to_exclude]
    all_potential_features = [col for col in df.columns if col != target_to_exclude]
    
    configs = []
    for col in features_to_impute:
        pred_features = [f for f in all_potential_features if f != col]
        
        # 1. Selalu tambahkan Regressor (Permintaan User)
        configs.append({
            'target': col,
            'method': 'regressor',
            'model_name': 'xgb',
            'pred_features': pred_features
        })
        
        # 2. Jika fitur adalah Biner (nunique < 3), tambahkan Classifier
        if df[col].dropna().nunique() < 3:
            # XGB Classifier
            configs.append({
                'target': col,
                'method': 'classifier',
                'model_name': 'xgb',
                'use_smote': False,
                'pred_features': pred_features
            })
            # RF Classifier
            configs.append({
                'target': col,
                'method': 'classifier',
                'model_name': 'rf',
                'use_smote': False,
                'pred_features': pred_features
            })
            
    return configs

if __name__ == '__main__':
    try:
        path = 'ml-service/data/credit_fraud.csv'
        df = pd.read_csv(path)
        
        print("Step 1: Cleaning Data Errors...")
        df_clean = clean_value_errors(df)
        
        # Cek missing value sebelum imputasi
        print("\nMissing values before imputation:")
        print(df_clean.isnull().sum()[df_clean.isnull().sum() > 0])
        
        print("\nStep 2: Generating Combined Imputation Configs...")
        configs = get_all_imputation_configs(df_clean, target_to_exclude='is_fraud')
        
        if not configs:
            print("No features need imputation.")
        else:
            print(f"Total experiment configs: {len(configs)}")
            
            print("\nStep 3: Evaluating All Imputation Methods (using Pipeline + Scaling)...")
            evaluate_imputation(df_clean, configs)
            
            print("\nStep 4: Applying Final Imputation (XGB Regression via Pipeline)...")
            # Jalankan regressor untuk aplikasi akhir (semua fitur)
            reg_configs = [c for c in configs if c['method'] == 'regressor']
            df_final = apply_imputation(df_clean, reg_configs)
            
            print(f"\nMissing values check after final imputation:")
            print(df_final.isnull().sum())
            
    except FileNotFoundError:
        print("Dataset not found. Please check the path.")
