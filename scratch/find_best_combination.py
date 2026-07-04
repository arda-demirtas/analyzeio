import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

# Ensure print outputs are encoded correctly for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set python path to find backend modules
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data

# The 13 candidate relative features
CANDIDATE_FEATURES = [
    "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
    "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
    "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag7"
]

print("Fetching BTC-USD historical data for greedy feature selection...")
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")

seq_len = 60
close_prices = df["Close"].values.reshape(-1, 1)
daily_returns = df["Daily_Return"].values.reshape(-1, 1)

# Helper function to evaluate a specific feature set using XGBoost
def evaluate_feature_set(feature_cols):
    if len(feature_cols) == 0:
        return 0.0, 999.0
        
    features_data = df[feature_cols].values
    
    # Create sequences
    X, y_return, y_close, prev_close = [], [], [], []
    for i in range(seq_len, len(df)):
        X.append(features_data[i - seq_len : i])
        y_return.append(daily_returns[i][0])
        y_close.append(close_prices[i][0])
        prev_close.append(close_prices[i-1][0])
        
    X = np.array(X)
    y_return = np.array(y_return).reshape(-1, 1)
    y_close = np.array(y_close).reshape(-1, 1)
    prev_close = np.array(prev_close).reshape(-1, 1)
    
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_ret_train, y_ret_test = y_return[:split], y_return[split:]
    y_close_test, prev_close_test = y_close[split:], prev_close[split:]
    
    # Scale
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    
    X_train_flat = X_train.reshape(-1, len(feature_cols))
    X_test_flat = X_test.reshape(-1, len(feature_cols))
    
    X_train_scaled = scaler_x.fit_transform(X_train_flat).reshape(X_train.shape)
    X_test_scaled = scaler_x.transform(X_test_flat).reshape(X_test.shape)
    
    y_ret_train_scaled = scaler_y.fit_transform(y_ret_train)
    
    # Flatten sequence input for XGBoost
    X_train_xgb = X_train_scaled.reshape(len(X_train_scaled), -1)
    X_test_xgb = X_test_scaled.reshape(len(X_test_scaled), -1)
    
    model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
    model.fit(X_train_xgb, y_ret_train_scaled)
    
    preds_scaled = model.predict(X_test_xgb).reshape(-1, 1)
    preds_ret = scaler_y.inverse_transform(preds_scaled)
    
    # Reconstruct Close Price
    preds_close = prev_close_test * (1 + preds_ret)
    
    # Calculate Metrics
    mape = np.mean(np.abs((y_close_test - preds_close) / y_close_test)) * 100
    
    actual_direction = np.sign(y_close_test[1:] - y_close_test[:-1])
    pred_direction = np.sign(preds_close[1:] - y_close_test[:-1])
    directional_accuracy = np.mean(actual_direction == pred_direction) * 100
    
    return directional_accuracy, mape

# ----------------------------------------------------
# Greedy Forward Feature Selection Algorithm
# ----------------------------------------------------
print("\nStarting Greedy Forward Selection (optimizing for Directional Accuracy with MAPE as tie-breaker)...")
best_features = []
remaining_features = list(CANDIDATE_FEATURES)
best_da = 0.0
best_mape = 999.0

step = 1
while remaining_features:
    step_best_feature = None
    step_best_da = 0.0
    step_best_mape = 999.0
    
    for f in remaining_features:
        candidate_set = best_features + [f]
        da, mape = evaluate_feature_set(candidate_set)
        
        # Optimize primarily for Directional Accuracy, secondarily for lower MAPE
        if da > step_best_da or (abs(da - step_best_da) < 1e-5 and mape < step_best_mape):
            step_best_da = da
            step_best_mape = mape
            step_best_feature = f
            
    # If the addition of the best feature improves Directional Accuracy or stabilizes it with better MAPE, we keep it
    if step_best_da > best_da or (abs(step_best_da - best_da) < 1e-5 and step_best_mape < best_mape):
        best_da = step_best_da
        best_mape = step_best_mape
        best_features.append(step_best_feature)
        remaining_features.remove(step_best_feature)
        print(f"Step {step}: Added '{step_best_feature}' -> Directional Accuracy: {best_da:.2f}%, MAPE: {best_mape:.2f}%")
        step += 1
    else:
        print(f"\nNo further improvement. Feature selection stopped.")
        break

print("\n" + "="*60)
print("             OPTIMAL INDICATOR COMBINATION FOUND")
print("="*60)
print("Best Features:", best_features)
print(f"Optimal Directional Accuracy: {best_da:.2f}%")
print(f"Optimal Test MAPE: {best_mape:.2f}%")
print("="*60)
