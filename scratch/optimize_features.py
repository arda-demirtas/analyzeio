import os
import sys
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

# 1. Fetch market data
df, asset_name, is_crypto, current_price = fetch_market_data("BTC-USD", interval="1d")
seq_length = 60
split_idx = int(len(df) * 0.8)
df_train = df.iloc[:split_idx]
df_test = df.iloc[split_idx - seq_length:]
max_ret = 0.15
min_ret = -0.15

# Align close prices for test set evaluation
prev_closes = df_test["Close"].values[seq_length - 1 : -1]
actual_closes = df_test["Close"].values[seq_length:]
y_test_raw = df_test["Daily_Return"].values[seq_length:]

def evaluate_metrics(actual_close, pred_close, actual_return, pred_return):
    rmse = float(np.sqrt(np.mean((pred_close - actual_close) ** 2)))
    mape = float(np.mean(np.abs((actual_close - pred_close) / actual_close)) * 100)
    act_dir = np.sign(actual_return)
    prd_dir = np.sign(pred_return)
    da = float(np.mean(act_dir == prd_dir) * 100)
    return rmse, mape, da

# Define indicator combinations to test
combinations = {
    "1_Current_2_feats": ["Return_Lag3", "EMA_50"],
    "2_Trend_Momentum_5_feats": ["EMA_20", "EMA_50", "RSI", "MACD", "MACD_Signal"],
    "3_Volatility_Volume_4_feats": ["ATR", "BB_Width", "Volume", "OBV"],
    "4_Full_Multivariate_10_feats": ["RSI", "MACD", "MACD_Hist", "EMA_20", "EMA_50", "BB_Width", "Volume", "ATR", "Return_Lag1", "Return_Lag3"],
    "5_Technical_Oscillators_10_feats": ["RSI", "MACD", "CCI", "Williams_R", "Stoch_K", "Stoch_D", "OBV", "BB_Width", "Return_Lag1", "Return_Lag3"],
    "6_Balanced_Subset_6_feats": ["RSI", "MACD_Hist", "EMA_20", "Volume", "ATR", "Return_Lag1"]
}

results = []

for name, features in combinations.items():
    print(f"\nEvaluating combination: {name} (features: {features})")
    
    # Drop rows with NaNs in the selected features for fair evaluation
    clean_cols = features + ["Daily_Return", "Close"]
    df_clean_train = df_train.dropna(subset=clean_cols)
    df_clean_test = df_test.dropna(subset=clean_cols)
    
    if len(df_clean_train) < 300 or len(df_clean_test) < seq_length + 20:
        print(f"Skipping {name} due to insufficient data after dropping NaNs.")
        continue

    # A. XGBoost Model Flow
    def make_sequences(x_data, y_data):
        xs, ys = [], []
        for i in range(seq_length, len(x_data)):
            xs.append(x_data[i-seq_length:i])
            ys.append(y_data[i])
        return np.array(xs).reshape(len(xs), -1), np.array(ys)
    
    x_xgb_train, y_xgb_train = make_sequences(df_clean_train[features].values, df_clean_train["Daily_Return"].values)
    x_xgb_test, y_xgb_test = make_sequences(df_clean_test[features].values, df_clean_test["Daily_Return"].values)
    
    scaler_x = StandardScaler()
    x_xgb_train_scaled = scaler_x.fit_transform(x_xgb_train)
    x_xgb_test_scaled = scaler_x.transform(x_xgb_test)
    
    model_xgb = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.03, random_state=42, n_jobs=-1)
    model_xgb.fit(x_xgb_train_scaled, y_xgb_train)
    pred_ret_xgb = np.clip(model_xgb.predict(x_xgb_test_scaled), min_ret, max_ret)
    
    # Align closes
    prev_closes_aligned = df_clean_test["Close"].values[seq_length - 1 : -1]
    actual_closes_aligned = df_clean_test["Close"].values[seq_length:]
    
    xgb_closes = prev_closes_aligned * (1 + pred_ret_xgb)
    xgb_rmse, xgb_mape, xgb_da = evaluate_metrics(actual_closes_aligned, xgb_closes, y_xgb_test, pred_ret_xgb)
    
    # B. Linear Regression (Ridge) Flow
    model_lr = Ridge(alpha=1.0)
    model_lr.fit(x_xgb_train_scaled, y_xgb_train)
    pred_ret_lr = np.clip(model_lr.predict(x_xgb_test_scaled), min_ret, max_ret)
    lr_closes = prev_closes_aligned * (1 + pred_ret_lr)
    lr_rmse, lr_mape, lr_da = evaluate_metrics(actual_closes_aligned, lr_closes, y_xgb_test, pred_ret_lr)
    
    # C. LSTM Model Flow
    # For LSTM, we need 3D input: (samples, timesteps, features)
    def prepare_lstm_data(data_df):
        xs, ys = [], []
        features_val = data_df[features].values
        returns_val = data_df["Daily_Return"].values
        
        scaler_x_lstm = StandardScaler()
        scaled_feats = scaler_x_lstm.fit_transform(features_val)
        scaler_y_lstm = StandardScaler()
        scaled_returns = scaler_y_lstm.fit_transform(returns_val.reshape(-1, 1))
        
        for i in range(seq_length, len(data_df)):
            xs.append(scaled_feats[i-seq_length:i])
            ys.append(scaled_returns[i][0])
            
        return np.array(xs), np.array(ys), scaler_x_lstm, scaler_y_lstm

    x_lstm_train, y_lstm_train, scaler_x_lstm, scaler_y_lstm = prepare_lstm_data(df_clean_train)
    
    # Test LSTM sequence preparation using training scaling
    test_feats_scaled = scaler_x_lstm.transform(df_clean_test[features].values)
    x_lstm_test = []
    for i in range(seq_length, len(df_clean_test)):
        x_lstm_test.append(test_feats_scaled[i-seq_length:i])
    x_lstm_test = np.array(x_lstm_test)
    
    model_lstm = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(features))),
        tf.keras.layers.LSTM(32, return_sequences=False),
        tf.keras.layers.Dense(1)
    ])
    model_lstm.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.005), loss="mse")
    model_lstm.fit(x_lstm_train, y_lstm_train, epochs=5, batch_size=64, verbose=0)
    
    pred_lstm_scaled = model_lstm.predict(x_lstm_test, verbose=0).flatten()
    pred_ret_lstm = np.clip(scaler_y_lstm.inverse_transform(pred_lstm_scaled.reshape(-1, 1)).flatten(), min_ret, max_ret)
    lstm_closes = prev_closes_aligned * (1 + pred_ret_lstm)
    lstm_rmse, lstm_mape, lstm_da = evaluate_metrics(actual_closes_aligned, lstm_closes, y_xgb_test, pred_ret_lstm)
    
    # Calculate Average Metrics across the 3 models
    avg_rmse = (xgb_rmse + lr_rmse + lstm_rmse) / 3
    avg_mape = (xgb_mape + lr_mape + lstm_mape) / 3
    avg_da = (xgb_da + lr_da + lstm_da) / 3
    
    results.append({
        "combination": name,
        "features_count": len(features),
        "xgb_rmse": xgb_rmse, "xgb_mape": xgb_mape, "xgb_da": xgb_da,
        "lr_rmse": lr_rmse, "lr_mape": lr_mape, "lr_da": lr_da,
        "lstm_rmse": lstm_rmse, "lstm_mape": lstm_mape, "lstm_da": lstm_da,
        "avg_rmse": avg_rmse, "avg_mape": avg_mape, "avg_da": avg_da
    })

# Output results as Markdown Table
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by="avg_rmse", ascending=True)

md_report = """# Optimal Features Selection Study for BTC-USD (XGBoost, LSTM, Linear Regression)

## 1. Average Model Performance by Feature Combination
*Sorted by Lowest Average RMSE*

| Rank | Combination Name | Features Count | Avg RMSE | Avg MAPE (%) | Avg Directional Accuracy (%) |
| :---: | :--- | :---: | :---: | :---: | :---: |
"""

for idx, row in enumerate(results_df.itertuples()):
    md_report += f"| {idx+1} | **{row.combination}** | {row.features_count} | ${row.avg_rmse:.2f} | {row.avg_mape:.2f}% | {row.avg_da:.2f}% |\n"

md_report += "\n## 2. Detailed Model Breakdown\n\n"
md_report += "| Combination Name | XGBoost RMSE / DA | LSTM RMSE / DA | Linear Reg RMSE / DA |\n"
md_report += "| :--- | :---: | :---: | :---: |\n"

for row in results_df.itertuples():
    md_report += f"| {row.combination} | ${row.xgb_rmse:.2f} / {row.xgb_da:.2f}% | ${row.lstm_rmse:.2f} / {row.lstm_da:.2f}% | ${row.lr_rmse:.2f} / {row.lr_da:.2f}% |\n"

report_path = "c:/Users/h1z1a/Desktop/Analyzeio/scratch/optimal_features_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(md_report)

print("\nStudy completed!")
print(f"Optimal features report saved to: {report_path}")
print("\n" + md_report)
