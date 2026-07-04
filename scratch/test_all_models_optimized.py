import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Ensure print outputs are encoded correctly for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set python path to find backend modules
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data
from backend.config import FEATURES

# Recommended features (excluding absolute price levels)
RECOMMENDED_FEATURES = [
    "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
    "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
    "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag7"
]

print("Starting Feature Optimization Comparison Test for LSTM, XGBoost, and Linear Regression...")

# ----------------------------------------------------
# 1. Fetch Data
# ----------------------------------------------------
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")
print(f"Data Loaded: {len(df)} rows.")

# ----------------------------------------------------
# Helper to train and evaluate a model
# ----------------------------------------------------
def evaluate_pipeline(feature_cols, model_type="xgboost"):
    seq_len = 60
    
    features_data = df[feature_cols].values
    close_prices = df["Close"].values.reshape(-1, 1)
    daily_returns = df["Daily_Return"].values.reshape(-1, 1)
    
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
    
    # Split
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
    
    # Train and predict
    if model_type == "lstm":
        # LSTM Model
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(seq_len, len(feature_cols))),
            tf.keras.layers.LSTM(units=50, return_sequences=False),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(units=25, activation="relu"),
            tf.keras.layers.Dense(units=1)
        ])
        model.compile(optimizer="adam", loss="mse")
        model.fit(X_train_scaled, y_ret_train_scaled, epochs=15, batch_size=32, verbose=0)
        
        preds_scaled = model.predict(X_test_scaled, verbose=0)
        preds_ret = scaler_y.inverse_transform(preds_scaled)
        
    elif model_type == "xgboost":
        # XGBoost Regressor (Requires flattening the sequence input to 2D)
        X_train_xgb = X_train_scaled.reshape(len(X_train_scaled), -1)
        X_test_xgb = X_test_scaled.reshape(len(X_test_scaled), -1)
        
        model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.05, random_state=42)
        model.fit(X_train_xgb, y_ret_train_scaled)
        
        preds_scaled = model.predict(X_test_xgb).reshape(-1, 1)
        preds_ret = scaler_y.inverse_transform(preds_scaled)
        
    elif model_type == "linear_regression":
        # Ridge Regression (Requires flattening the sequence input to 2D)
        X_train_lr = X_train_scaled.reshape(len(X_train_scaled), -1)
        X_test_lr = X_test_scaled.reshape(len(X_test_scaled), -1)
        
        model = Ridge(alpha=10000.0)
        model.fit(X_train_lr, y_ret_train_scaled)
        
        preds_scaled = model.predict(X_test_lr).reshape(-1, 1)
        preds_ret = scaler_y.inverse_transform(preds_scaled)
        
    # Reconstruct Close Price
    preds_close = prev_close_test * (1 + preds_ret)
    
    # Calculate Metrics
    rmse = np.sqrt(np.mean((preds_close - y_close_test) ** 2))
    mape = np.mean(np.abs((y_close_test - preds_close) / y_close_test)) * 100
    
    actual_direction = np.sign(y_close_test[1:] - y_close_test[:-1])
    pred_direction = np.sign(preds_close[1:] - y_close_test[:-1])
    directional_accuracy = np.mean(actual_direction == pred_direction) * 100
    
    return rmse, mape, directional_accuracy

# ----------------------------------------------------
# 2. Run Evaluations
# ----------------------------------------------------
models = ["lstm", "xgboost", "linear_regression"]
results = []

for m in models:
    print(f"\nEvaluating {m.upper()} under original features (19 features)...")
    rmse_orig, mape_orig, da_orig = evaluate_pipeline(FEATURES, model_type=m)
    
    print(f"Evaluating {m.upper()} under optimized features (13 features)...")
    rmse_opt, mape_opt, da_opt = evaluate_pipeline(RECOMMENDED_FEATURES, model_type=m)
    
    results.append({
        "Model": m.upper(),
        "Orig_RMSE": rmse_orig,
        "Opt_RMSE": rmse_opt,
        "Orig_MAPE": mape_orig,
        "Opt_MAPE": mape_opt,
        "Orig_DA": da_orig,
        "Opt_DA": da_opt
    })

# ----------------------------------------------------
# 3. Print Results Comparison Table
# ----------------------------------------------------
print("\n" + "="*80)
print("             FEATURE OPTIMIZATION COMPARISON TEST RESULTS")
print("="*80)
print(f"{'MODEL':<20} | {'CONFIG':<12} | {'RMSE':<12} | {'MAPE':<10} | {'DIR. ACC.':<10}")
print("-"*80)

for r in results:
    print(f"{r['Model']:<20} | {'Original':<12} | {r['Orig_RMSE']:<12.2f} | {r['Orig_MAPE']:<9.2f}% | {r['Orig_DA']:<9.2f}%")
    print(f"{'':<20} | {'Optimized':<12} | {r['Opt_RMSE']:<12.2f} | {r['Opt_MAPE']:<9.2f}% | {r['Opt_DA']:<9.2f}%")
    print("-"*80)
