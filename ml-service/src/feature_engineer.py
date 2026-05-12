import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
class FraudFeatureEngineer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X):
        X_eng = X.copy()
        
        # 1. Ratio Transaction to Balance
        X_eng['tx_balance_ratio'] = X_eng['transaction_amount'] / (X_eng['account_balance'] + 1)
        
        # 2. Distance & Risk interaction
        X_eng['dist_risk_score'] = X_eng['merchant_distance_km'] * X_eng['merchant_risk_score']
        
        # 3. Cyclical Time (Hour)
        X_eng['sin_hour'] = np.sin(2 * np.pi * X_eng['transaction_hour'] / 24)
        X_eng['cos_hour'] = np.cos(2 * np.pi * X_eng['transaction_hour'] / 24)
        
        # 4. Late Night Flag (0-4 AM)
        X_eng['is_late_night'] = X_eng['transaction_hour'].apply(lambda x: 1 if x <= 4 else 0)
        
        return X_eng
