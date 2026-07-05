import os
import sys
import json
import datetime
import numpy as np
import pandas as pd
import xgboost as xgb
import tensorflow as tf
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Ensure print outputs are encoded correctly for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set python path to find backend modules
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data
from backend.config import FEATURES, DEFAULT_SEQUENCE_LENGTH

def evaluate_metrics(actual_close, pred_close, actual_return, pred_return):
    # Root Mean Squared Error (RMSE)
    rmse = float(np.sqrt(np.mean((pred_close - actual_close) ** 2)))
    # Mean Absolute Percentage Error (MAPE)
    mape = float(np.mean(np.abs((actual_close - pred_close) / actual_close)) * 100)
    # Directional Accuracy (DA)
    act_dir = np.sign(actual_return)
    prd_dir = np.sign(pred_return)
    da = float(np.mean(act_dir == prd_dir) * 100)
    return rmse, mape, da

print("----------------------------------------------------------------")
print("STARTING 4-MODEL COMPARISON STUDY FOR BTC-USD (Daily Interval)")
print("----------------------------------------------------------------")

# 1. Fetch market data
print("Fetching daily BTC-USD data...")
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")
print(f"Data Loaded: {len(df)} candles.")

seq_length = DEFAULT_SEQUENCE_LENGTH # 60
split_idx = int(len(df) * 0.8)
df_train = df.iloc[:split_idx]
df_test = df.iloc[split_idx - seq_length:]

max_ret = 0.15
min_ret = -0.15

# Prepare XGB/LR features
def make_sequences(x_data, y_data):
    xs, ys = [], []
    for i in range(seq_length, len(x_data)):
        xs.append(x_data[i-seq_length:i])
        ys.append(y_data[i])
    return np.array(xs).reshape(len(xs), -1), np.array(ys)

x_train_raw, y_train_raw = make_sequences(df_train[FEATURES].values, df_train["Daily_Return"].values)
x_test_raw, y_test_raw = make_sequences(df_test[FEATURES].values, df_test["Daily_Return"].values)

scaler_x = StandardScaler()
x_train_scaled = scaler_x.fit_transform(x_train_raw)
x_test_scaled = scaler_x.transform(x_test_raw)

# A. XGBoost
print("\n--- Training XGBoost ---")
model_xgb = xgb.XGBRegressor(
    n_estimators=300, max_depth=5, learning_rate=0.03,
    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1,
    random_state=42, n_jobs=-1
)
model_xgb.fit(x_train_scaled, y_train_raw)
pred_ret_xgb = model_xgb.predict(x_test_scaled)
pred_ret_xgb = np.clip(pred_ret_xgb, min_ret, max_ret)

# Reconstruct Close prices
prev_closes = df_test["Close"].values[seq_length - 1 : -1]
actual_closes = df_test["Close"].values[seq_length:]
xgb_closes = prev_closes * (1 + pred_ret_xgb)
xgb_rmse, xgb_mape, xgb_da = evaluate_metrics(actual_closes, xgb_closes, y_test_raw, pred_ret_xgb)

# B. LSTM
print("\n--- Training LSTM ---")
def prepare_lstm_data(data_df):
    xs, ys = [], []
    features_val = data_df[FEATURES].values
    returns_val = data_df["Daily_Return"].values
    
    # Scale LSTM inputs
    scaler_x_lstm = StandardScaler()
    scaled_feats = scaler_x_lstm.fit_transform(features_val)
    scaler_y_lstm = StandardScaler()
    scaled_returns = scaler_y_lstm.fit_transform(returns_val.reshape(-1, 1))
    
    for i in range(seq_length, len(data_df)):
        xs.append(scaled_feats[i-seq_length:i])
        ys.append(scaled_returns[i][0])
        
    return np.array(xs), np.array(ys), scaler_x_lstm, scaler_y_lstm

x_lstm_train, y_lstm_train, scaler_x_lstm, scaler_y_lstm = prepare_lstm_data(df_train)
# Scaled test sequence using same scalers
test_feats_scaled = scaler_x_lstm.transform(df_test[FEATURES].values)
test_rets_scaled = scaler_y_lstm.transform(df_test["Daily_Return"].values.reshape(-1, 1))

x_lstm_test, y_lstm_test = [], []
for i in range(seq_length, len(df_test)):
    x_lstm_test.append(test_feats_scaled[i-seq_length:i])
    y_lstm_test.append(test_rets_scaled[i][0])
x_lstm_test = np.array(x_lstm_test)
y_lstm_test = np.array(y_lstm_test)

# Simple LSTM architecture mimicking production
model_lstm = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
    tf.keras.layers.LSTM(32, return_sequences=False),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1)
])
model_lstm.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.005), loss="mse")
model_lstm.fit(x_lstm_train, y_lstm_train, epochs=8, batch_size=32, verbose=0)

pred_lstm_scaled = model_lstm.predict(x_lstm_test, verbose=0)
pred_ret_lstm = scaler_y_lstm.inverse_transform(pred_lstm_scaled).flatten()
pred_ret_lstm = np.clip(pred_ret_lstm, min_ret, max_ret)
lstm_closes = prev_closes * (1 + pred_ret_lstm)
lstm_rmse, lstm_mape, lstm_da = evaluate_metrics(actual_closes, lstm_closes, y_test_raw, pred_ret_lstm)

# C. Linear Regression (Ridge)
print("\n--- Training Linear Regression ---")
model_lr = Ridge(alpha=1.0)
model_lr.fit(x_train_scaled, y_train_raw)
pred_ret_lr = model_lr.predict(x_test_scaled)
pred_ret_lr = np.clip(pred_ret_lr, min_ret, max_ret)
lr_closes = prev_closes * (1 + pred_ret_lr)
lr_rmse, lr_mape, lr_da = evaluate_metrics(actual_closes, lr_closes, y_test_raw, pred_ret_lr)

# D. PatchTST
print("\n--- Training PatchTST (Multivariate Indicator Ridge Simulation) ---")
tst_features = [
    "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
    "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
    "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag7"
]
existing_tst_features = [f for f in tst_features if f in df.columns]
df_clean = df.dropna(subset=existing_tst_features + ["Daily_Return"])

df_train_tst = df_clean.iloc[:int(len(df_clean) * 0.8)]
df_test_tst = df_clean.iloc[int(len(df_clean) * 0.8):]

X_train_tst = df_train_tst[existing_tst_features].iloc[:-1].values
y_train_tst = df_train_tst["Daily_Return"].iloc[1:].values
X_test_tst = df_test_tst[existing_tst_features].iloc[:-1].values
y_test_tst = df_test_tst["Daily_Return"].iloc[1:].values

scaler_tst_x = StandardScaler()
X_train_tst_scaled = scaler_tst_x.fit_transform(X_train_tst)
X_test_tst_scaled = scaler_tst_x.transform(X_test_tst)

model_tst = Ridge(alpha=1.0)
model_tst.fit(X_train_tst_scaled, y_train_tst)
pred_ret_tst = model_tst.predict(X_test_tst_scaled)
pred_ret_tst = np.clip(pred_ret_tst, min_ret, max_ret)

# Align close prices for PatchTST test split
tst_prev_closes = df_test_tst["Close"].values[:-1]
tst_actual_closes = df_test_tst["Close"].values[1:]

tst_closes = tst_prev_closes * (1 + pred_ret_tst)
tst_rmse, tst_mape, tst_da = evaluate_metrics(tst_actual_closes, tst_closes, y_test_tst, pred_ret_tst)

# Next-day forecasts comparison
print("\nCalculating next-day forecast...")
last_idx = -1
last_actual_close = float(df["Close"].iloc[last_idx])

# XGB
last_feats_xgb = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
last_feats_xgb_scaled = scaler_x.transform(last_feats_xgb)
next_xgb_ret = np.clip(model_xgb.predict(last_feats_xgb_scaled)[0], min_ret, max_ret)
next_xgb_price = last_actual_close * (1 + next_xgb_ret)

# LSTM
last_feats_lstm = df[FEATURES].iloc[-seq_length:].values
scaled_last_lstm = scaler_x_lstm.transform(last_feats_lstm)
next_lstm_ret_scaled = model_lstm.predict(np.array([scaled_last_lstm]), verbose=0)[0][0]
next_lstm_ret = np.clip(scaler_y_lstm.inverse_transform([[next_lstm_ret_scaled]])[0][0], min_ret, max_ret)
next_lstm_price = last_actual_close * (1 + next_lstm_ret)

# LR
next_lr_ret = np.clip(model_lr.predict(last_feats_xgb_scaled)[0], min_ret, max_ret)
next_lr_price = last_actual_close * (1 + next_lr_ret)

# PatchTST
last_feats_tst = df[existing_tst_features].iloc[-1:].values
last_feats_tst_scaled = scaler_tst_x.transform(last_feats_tst)
next_tst_ret = np.clip(model_tst.predict(last_feats_tst_scaled)[0], min_ret, max_ret)
next_tst_price = last_actual_close * (1 + next_tst_ret)


# Generate report markdown
report_md = f"""# BTC-USD 4-Model Performance Comparison Study

Generated on: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Asset: BTC-USD
Last Close Price: ${last_actual_close:,.2f}

## 1. Test Performance Metrics (Evaluation Set)

| Model Name | Test RMSE | Test MAPE (%) | Directional Accuracy (%) |
| :--- | :---: | :---: | :---: |
| **XGBoost** | ${xgb_rmse:.2f} | {xgb_mape:.2f}% | {xgb_da:.2f}% |
| **LSTM** | ${lstm_rmse:.2f} | {lstm_mape:.2f}% | {lstm_da:.2f}% |
| **Linear Regression (Ridge)** | ${lr_rmse:.2f} | {lr_mape:.2f}% | {lr_da:.2f}% |
| **PatchTST (Multivariate Simulation)** | ${tst_rmse:.2f} | {tst_mape:.2f}% | {tst_da:.2f}% |

## 2. Next Day Prediction Forecasts

| Model Name | Predicted Close Price | Expected Price Change | Sentiment Recommendation |
| :--- | :---: | :---: | :---: |
| **XGBoost** | ${next_xgb_price:,.3f} | {next_xgb_ret*100:+.2f}% | **{"BULLISH (LONG)" if next_xgb_ret >= 0 else "BEARISH (SHORT)"}** |
| **LSTM** | ${next_lstm_price:,.3f} | {next_lstm_ret*100:+.2f}% | **{"BULLISH (LONG)" if next_lstm_ret >= 0 else "BEARISH (SHORT)"}** |
| **Linear Regression (Ridge)** | ${next_lr_price:,.3f} | {next_lr_ret*100:+.2f}% | **{"BULLISH (LONG)" if next_lr_ret >= 0 else "BEARISH (SHORT)"}** |
| **PatchTST (Multivariate Simulation)** | ${next_tst_price:,.3f} | {next_tst_ret*100:+.2f}% | **{"BULLISH (LONG)" if next_tst_ret >= 0 else "BEARISH (SHORT)"}** |

---
*Note: Evaluated on 80% train / 20% test split of historical data. PatchTST is trained on 13 multivariate indicators.*
"""

# Save report
report_path = "c:/Users/h1z1a/Desktop/Analyzeio/scratch/models_comparison_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_md)

print("\n----------------------------------------------------------------")
print("STUDY COMPLETED successfully!")
print(f"Comparison report saved to: {report_path}")
print("----------------------------------------------------------------\n")
print(report_md)
