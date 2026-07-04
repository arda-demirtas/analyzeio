import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Ensure print outputs are encoded correctly for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set python path to find backend modules
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data
from backend.config import FEATURES

print("Fetching BTC-USD historical data to analyze feature importance...")
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")

# Prepare X and y
X = df[FEATURES]
y = df["Daily_Return"].shift(-1) # Target is next day's percentage return

# Drop the last row because y is NaN
X = X.iloc[:-1]
y = y.dropna()

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train XGBoost regressor
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.05,
    random_state=42
)
model.fit(X_train, y_train)

# Calculate feature importance
importances = model.feature_importances_
feature_imp_df = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": importances
}).sort_values(by="Importance", ascending=False)

print("\n--- Feature Importance Analysis Results ---")
for idx, row in feature_imp_df.iterrows():
    print(f"{row['Feature']}: {row['Importance']:.4f} ({row['Importance']*100:.2f}%)")

# Filter out features with low importance (e.g., < 1%)
threshold = 0.0100
low_importance_features = feature_imp_df[feature_imp_df["Importance"] < threshold]

print("\n--- Recommended Features to Remove (Importance < 1.00%) ---")
if not low_importance_features.empty:
    for idx, row in low_importance_features.iterrows():
        print(f"- {row['Feature']} (Importance: {row['Importance']*100:.2f}%)")
else:
    print("All features are above threshold.")
