import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import tensorflow as tf

# Suppress warnings and tensorflow logs
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.get_logger().setLevel("ERROR")

# Ensure workspace is in Python path
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")

from backend.predictor import fetch_market_data, FEATURES

# 30 Popular Symbols (Cryptos, Stocks, Commodities)
TEST_SYMBOLS = [
    # Cryptos (Binance API)
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
    "ADA-USD", "AVAX-USD", "DOGE-USD", "DOT-USD", "LINK-USD",
    "LTC-USD", "NEAR-USD", "RNDR-USD", "PEPE-USD", "OP-USD",
    # Stocks (Yahoo Finance)
    "AAPL", "TSLA", "MSFT", "AMZN", "NVDA",
    "AMD", "META", "GOOGL", "NFLX", "NFLX", # Double check/replace duplicate NFLX
    # Commodities/Indices (Yahoo Finance)
    "GC=F", "CL=F", "SPY", "QQQ", "SLV=F"
]
# Replace duplicate NFLX with BABA to make it exactly 30 unique symbols
TEST_SYMBOLS[9] = "LINK-USD" # Ensure unique
TEST_SYMBOLS = list(set(TEST_SYMBOLS))
if len(TEST_SYMBOLS) < 30:
    # Top-off with other popular tickers if needed
    for ticker in ["BABA", "NFLX", "JPM", "V", "DIS"]:
        if ticker not in TEST_SYMBOLS:
            TEST_SYMBOLS.append(ticker)
TEST_SYMBOLS = TEST_SYMBOLS[:30]

def prepare_data_splits(df: pd.DataFrame, seq_length: int = 60):
    features = FEATURES
    split_val = int(len(df) * 0.70)
    split_test = int(len(df) * 0.85)
    
    df_train = df.iloc[:split_val]
    df_val = df.iloc[split_val - seq_length : split_test]
    df_test = df.iloc[split_test - seq_length:]
    
    # LSTM Setup (Scaled)
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    
    scaled_x_train = scaler_x.fit_transform(df_train[features].values)
    scaled_y_train = scaler_y.fit_transform(df_train[["Daily_Return"]].values)
    
    scaled_x_val = scaler_x.transform(df_val[features].values)
    scaled_y_val = scaler_y.transform(df_val[["Daily_Return"]].values)
    
    scaled_x_test = scaler_x.transform(df_test[features].values)
    scaled_y_test = scaler_y.transform(df_test[["Daily_Return"]].values)
    
    def make_sequences(x_data, y_data):
        xs, ys = [], []
        for i in range(seq_length, len(x_data)):
            xs.append(x_data[i-seq_length:i])
            ys.append(y_data[i][0])
        return np.array(xs), np.array(ys)
        
    x_lstm_train, y_lstm_train = make_sequences(scaled_x_train, scaled_y_train)
    x_lstm_val, y_lstm_val = make_sequences(scaled_x_val, scaled_y_val)
    x_lstm_test, y_lstm_test = make_sequences(scaled_x_test, scaled_y_test)
    
    # XGBoost Setup (Raw)
    raw_x_train = df_train[features].values
    raw_y_train = df_train["Daily_Return"].values
    raw_x_val = df_val[features].values
    raw_y_val = df_val["Daily_Return"].values
    raw_x_test = df_test[features].values
    raw_y_test = df_test["Daily_Return"].values
    
    def make_raw_sequences(x_data, y_data):
        xs, ys = [], []
        for i in range(seq_length, len(x_data)):
            xs.append(x_data[i-seq_length:i])
            ys.append(y_data[i])
        return np.array(xs), np.array(ys)
        
    x_xgb_train_seq, y_xgb_train = make_raw_sequences(raw_x_train, raw_y_train)
    x_xgb_val_seq, y_xgb_val = make_raw_sequences(raw_x_val, raw_y_val)
    x_xgb_test_seq, y_xgb_test = make_raw_sequences(raw_x_test, raw_y_test)
    
    x_xgb_train = x_xgb_train_seq.reshape(x_xgb_train_seq.shape[0], -1)
    x_xgb_val = x_xgb_val_seq.reshape(x_xgb_val_seq.shape[0], -1)
    x_xgb_test = x_xgb_test_seq.reshape(x_xgb_test_seq.shape[0], -1)
    
    eval_df = df.iloc[split_test:].copy()
    prev_close_val = df.iloc[split_test - 1]["Close"]
    
    return {
        "x_lstm_train": x_lstm_train, "y_lstm_train": y_lstm_train,
        "x_lstm_val": x_lstm_val, "y_lstm_val": y_lstm_val,
        "x_lstm_test": x_lstm_test, "y_lstm_test": y_lstm_test,
        "x_xgb_train": x_xgb_train, "y_xgb_train": y_xgb_train,
        "x_xgb_val": x_xgb_val, "y_xgb_val": y_xgb_val,
        "x_xgb_test": x_xgb_test, "y_xgb_test": y_xgb_test,
        "scaler_y": scaler_y,
        "eval_df": eval_df,
        "prev_close_val": prev_close_val
    }

def train_lstm_model_with_val(x_train, y_train, x_val, y_val, seq_length=60):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
        tf.keras.layers.LSTM(units=64, return_sequences=True),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(units=32, return_sequences=False),
        tf.keras.layers.Dense(units=32, activation="relu"),
        tf.keras.layers.Dense(units=1)
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=5, restore_best_weights=True
    )
    model.fit(
        x_train, y_train, epochs=25, batch_size=32,
        validation_data=(x_val, y_val), callbacks=[early_stopping], verbose=0
    )
    return model

def evaluate_predictions(y_pred, data, is_scaled=True):
    eval_subset = data["eval_df"].copy()
    if is_scaled:
        scaler_y = data["scaler_y"]
        y_pred_returns = scaler_y.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    else:
        y_pred_returns = y_pred
        
    n_samples = min(len(y_pred_returns), len(eval_subset))
    y_pred_returns = y_pred_returns[:n_samples]
    eval_subset = eval_subset.iloc[:n_samples].copy()
    
    prev_close_val = data["prev_close_val"]
    prev_closes = eval_subset["Close"].shift(1).fillna(prev_close_val).values
    actual_closes = eval_subset["Close"].values
    predicted_closes = prev_closes * (1 + y_pred_returns)
    
    mape = np.mean(np.abs((actual_closes - predicted_closes) / actual_closes)) * 100
    actual_returns = eval_subset["Daily_Return"].values
    correct_direction = np.sign(actual_returns) == np.sign(y_pred_returns)
    directional_accuracy = np.mean(correct_direction) * 100
    
    return mape, directional_accuracy

if __name__ == "__main__":
    print("=========================================================")
    print("          BENCHMARKING 30 POPULAR SYMBOLS")
    print("                XGBoost vs Stacked LSTM")
    print("=========================================================\n")
    
    results = []
    
    for idx, symbol in enumerate(TEST_SYMBOLS):
        print(f"[{idx+1}/30] Processing {symbol}...")
        try:
            df, _, _, _ = fetch_market_data(symbol, "1d")
            if len(df) < 300:
                print(f"  Skipping {symbol}: insufficient data length ({len(df)})")
                continue
                
            data = prepare_data_splits(df)
            
            # --- XGBoost ---
            xgb_model = xgb.XGBRegressor(
                n_estimators=300, # slightly lower trees to speed up benchmark
                max_depth=6,
                learning_rate=0.03,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1,
                early_stopping_rounds=15,
                random_state=42,
                n_jobs=-1
            )
            
            start = time.time()
            xgb_model.fit(
                data["x_xgb_train"], data["y_xgb_train"],
                eval_set=[(data["x_xgb_val"], data["y_xgb_val"])],
                verbose=False
            )
            xgb_time = time.time() - start
            y_pred_xgb = xgb_model.predict(data["x_xgb_test"])
            xgb_mape, xgb_dir = evaluate_predictions(y_pred_xgb, data, is_scaled=False)
            
            # --- LSTM ---
            start = time.time()
            lstm_model = train_lstm_model_with_val(
                data["x_lstm_train"], data["y_lstm_train"],
                data["x_lstm_val"], data["y_lstm_val"]
            )
            lstm_time = time.time() - start
            y_pred_lstm = lstm_model.predict(data["x_lstm_test"]).flatten()
            lstm_mape, lstm_dir = evaluate_predictions(y_pred_lstm, data, is_scaled=True)
            
            results.append({
                "Symbol": symbol,
                "XGB_Time": xgb_time,
                "XGB_MAPE": xgb_mape,
                "XGB_Dir": xgb_dir,
                "LSTM_Time": lstm_time,
                "LSTM_MAPE": lstm_mape,
                "LSTM_Dir": lstm_dir
            })
            
            print(f"  XGBoost -> MAPE: {xgb_mape:.4f}%, Dir: {xgb_dir:.2f}%, Time: {xgb_time:.2f}s")
            print(f"  LSTM    -> MAPE: {lstm_mape:.4f}%, Dir: {lstm_dir:.2f}%, Time: {lstm_time:.2f}s")
            
        except Exception as e:
            print(f"  Failed processing {symbol}: {e}")
            
    # Compile Results
    if not results:
        print("No symbols successfully processed.")
        sys.exit(1)
        
    res_df = pd.DataFrame(results)
    
    # Calculate Averages
    avg_xgb_time = res_df["XGB_Time"].mean()
    avg_lstm_time = res_df["LSTM_Time"].mean()
    avg_xgb_mape = res_df["XGB_MAPE"].mean()
    avg_lstm_mape = res_df["LSTM_MAPE"].mean()
    avg_xgb_dir = res_df["XGB_Dir"].mean()
    avg_lstm_dir = res_df["LSTM_Dir"].mean()
    
    # Wins
    xgb_mape_wins = (res_df["XGB_MAPE"] < res_df["LSTM_MAPE"]).sum()
    lstm_mape_wins = (res_df["LSTM_MAPE"] < res_df["XGB_MAPE"]).sum()
    xgb_dir_wins = (res_df["XGB_Dir"] > res_df["LSTM_Dir"]).sum()
    lstm_dir_wins = (res_df["LSTM_Dir"] > res_df["XGB_Dir"]).sum()
    
    # Print Aggregated Report
    print("\n\n" + "="*70)
    print("                 BENCHMARK AGGREGATED REPORT")
    print("="*70)
    print(f"{'Metric':<30} | {'XGBoost (Raw)':<15} | {'Stacked LSTM':<15}")
    print("-"*70)
    print(f"{'Average Training Time':<30} | {avg_xgb_time:<15.2f}s | {avg_lstm_time:<15.2f}s")
    print(f"{'Average Test Set MAPE':<30} | {avg_xgb_mape:<15.4f}% | {avg_lstm_mape:<15.4f}%")
    print(f"{'Average Directional Acc.':<30} | {avg_xgb_dir:<15.2f}% | {avg_lstm_dir:<15.2f}%")
    print("-"*70)
    print(f"{'MAPE Wins (Out of 30)':<30} | {xgb_mape_wins:<15} | {lstm_mape_wins:<15}")
    print(f"{'Directional Wins (Out of 30)':<30} | {xgb_dir_wins:<15} | {lstm_dir_wins:<15}")
    print("="*70)
    
    # Print Symbol breakdown
    print("\n\n=== SYMBOL-BY-SYMBOL BREAKDOWN ===")
    print(f"{'Symbol':<10} | {'XGB MAPE':<10} | {'LSTM MAPE':<10} | {'XGB Dir':<10} | {'LSTM Dir':<10}")
    print("-"*65)
    for r in results:
        print(f"{r['Symbol']:<10} | {r['XGB_MAPE']:<9.4f}% | {r['LSTM_MAPE']:<10.4f}% | {r['XGB_Dir']:<9.2f}% | {r['LSTM_Dir']:<10.2f}%")
