import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from xgboost import XGBRegressor, XGBClassifier
from feature_engineer import FraudFeatureEngineer

class FraudDataCleaner(BaseEstimator, TransformerMixin):
    """
    Transformer untuk membersihkan data kotor (negatif age, string _err, dll).
    """
    def __init__(self):
        self.numeric_cols = ['age', 'transaction_amount', 'account_balance', 'transaction_hour', 'num_transactions_today']

    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X):
        X_clean = X.copy()
        
        # 1. Bersihkan akhiran '_err' dan konversi ke numeric
        for col in X_clean.columns:
            if X_clean[col].dtype == object:
                mask = X_clean[col].str.contains('_err', na=False)
                if mask.any():
                    X_clean.loc[mask, col] = X_clean.loc[mask, col].str.replace('_err', '', regex=False)
            
            if col in self.numeric_cols:
                X_clean[col] = pd.to_numeric(X_clean[col], errors='coerce')

        # 2. Handle anomali spesifik
        if 'age' in X_clean.columns:
            X_clean.loc[X_clean['age'] < 0, 'age'] = np.nan

        if 'account_balance' in X_clean.columns:
            X_clean.loc[X_clean['account_balance'] == -99999.0, 'account_balance'] = np.nan

        if 'transaction_hour' in X_clean.columns:
            mask_hour = (X_clean['transaction_hour'] < 0) | (X_clean['transaction_hour'] > 23)
            X_clean.loc[mask_hour, 'transaction_hour'] = np.nan

        return X_clean

class XGBPredictiveImputer(BaseEstimator, TransformerMixin):
    """
    Transformer yang menggunakan XGBoost Regression untuk mengisi missing values.
    Melatih model untuk setiap fitur yang memiliki NaN saat fit().
    """
    def __init__(self, model_params=None):
        self.model_params = model_params if model_params else {'n_estimators': 50, 'random_state': 42}
        self.models = {}
        self.cols_to_impute = []

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X)
        self.cols_to_impute = X_df.columns[X_df.isnull().any()].tolist()
        
        for col in self.cols_to_impute:
            # Fitur lain sebagai prediktor
            pred_features = [f for f in X_df.columns if f != col]
            
            # Data untuk training imputer (target tidak NaN)
            train_data = X_df[X_df[col].notna()]
            if train_data.empty: continue
            
            X_train = train_data[pred_features]
            y_train = train_data[col]
            
            model = XGBRegressor(**self.model_params)
            model.fit(X_train, y_train)
            self.models[col] = model
            
        return self

    def transform(self, X):
        X_imputed = pd.DataFrame(X).copy()
        
        for col, model in self.models.items():
            predict_mask = X_imputed[col].isna()
            if predict_mask.any():
                pred_features = [f for f in X_imputed.columns if f != col]
                X_predict = X_imputed.loc[predict_mask, pred_features]
                
                preds = model.predict(X_predict)
                
                # Rounding logic untuk kolom tertentu
                if col in ['age', 'transaction_hour', 'num_transactions_today', 'is_foreign_transaction', 'prev_fraud_flag']:
                    preds = np.round(preds).astype(int)
                    if col in ['is_foreign_transaction', 'prev_fraud_flag']:
                        preds = np.clip(preds, 0, 1)
                
                X_imputed.loc[predict_mask, col] = preds
                
        # Fallback untuk nilai yang masih NaN (jika ada fitur baru yang semua NaN)
        if X_imputed.isnull().any().any():
            X_imputed = X_imputed.fillna(0)
            
        return X_imputed

def build_fraud_pipeline():
    """
    Membangun pipeline lengkap: Clean -> Impute -> Scale -> Classify.
    """
    pipeline = Pipeline([
        ('cleaner', FraudDataCleaner()),
        ('imputer', XGBPredictiveImputer()),
        ('feature_eng', FraudFeatureEngineer()),
        ('scaler', StandardScaler()),
        ('classifier', XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric='logloss', random_state=42))
    ])
    return pipeline

# if __name__ == '__main__':
#     try:
#         # Load Data
#         df = pd.read_csv('ml-service/data/credit_fraud.csv')
#         X = df.drop('is_fraud', axis=1)
#         y = df['is_fraud']
        
#         # Split Data (Train, Val, Test)
#         X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
#         X_train, X_val, y_train, y_val = train_test_split(X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full) # 0.25 * 0.8 = 0.2
        
#         print(f"Data Shapes: Train={X_train.shape}, Val={X_val.shape}, Test={X_test.shape}")
        
#         # Build Pipeline
#         pipeline = build_fraud_pipeline()
        
#         # Training
#         print("\nStep 1: Training Full Pipeline (Cleaning + Imputation + Scaling + Model)...")
#         pipeline.fit(X_train, y_train)
        
#         # Evaluation on Validation Set
#         print("\nStep 2: Evaluating on Validation Set (Missing values filled automatically)...")
#         y_val_pred = pipeline.predict(X_val)
#         print("\nValidation Results:")
#         print(classification_report(y_val, y_val_pred))
        
#         # Evaluation on Test Set
#         print("\nStep 3: Final Testing on Test Set...")
#         y_test_pred = pipeline.predict(X_test)
#         print("\nTest Results:")
#         print(classification_report(y_test, y_test_pred))
        
#         f1 = f1_score(y_test, y_test_pred)
#         print(f"\nFinal Test F1-Score: {f1:.4f}")
        
#         # Pipeline check
#         print("\nPipeline check: All missing values handled? ", end="")
#         X_test_processed = pipeline.named_steps['imputer'].transform(pipeline.named_steps['cleaner'].transform(X_test))
#         print(not X_test_processed.isnull().any().any())

#     except FileNotFoundError:
#         print("Dataset not found. Please check 'ml-service/data/credit_fraud.csv'.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
