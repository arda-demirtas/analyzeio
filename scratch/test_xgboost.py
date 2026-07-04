import os
import sys
import time
import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import tensorflow as tf

# Ensure workspace is in Python path
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")

from backend.predictor import fetch_market_data, FEATURES

def prepare_data_splits(df: pd.DataFrame, seq_length: int = 60):
    """
    Splits data chronologically into Train (70%), Val (15%), and Test (15%).
    - For LSTM: X and y are scaled using MinMaxScaler.
    - For XGBoost: X and y are kept RAW (unscaled) to match tree model preference.
    """
    features = FEATURES
    
    # Chronological Split Slices
    split_val = int(len(df) * 0.70)
    split_test = int(len(df) * 0.85)
    
    df_train = df.iloc[:split_val]
    df_val = df.iloc[split_val - seq_length : split_test]
    df_test = df.iloc[split_test - seq_length:]
    
    # --- 1. LSTM Data Setup (Scaled) ---
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    
    # Fit scalers only on training data (no data leakage)
    train_x_raw = df_train[features].values
    train_y_raw = df_train[["Daily_Return"]].values
    
    scaled_x_train = scaler_x.fit_transform(train_x_raw)
    scaled_y_train = scaler_y.fit_transform(train_y_raw)
    
    # Transform validation and test data using training parameters
    scaled_x_val = scaler_x.transform(df_val[features].values)
    scaled_y_val = scaler_y.transform(df_val[["Daily_Return"]].values)
    
    scaled_x_test = scaler_x.transform(df_test[features].values)
    scaled_y_test = scaler_y.transform(df_test[["Daily_Return"]].values)
    
    # Helper to construct 3D sliding window sequences
    def make_sequences(x_data, y_data):
        xs, ys = [], []
        for i in range(seq_length, len(x_data)):
            xs.append(x_data[i-seq_length:i])
            ys.append(y_data[i][0])
        return np.array(xs), np.array(ys)
        
    x_lstm_train, y_lstm_train = make_sequences(scaled_x_train, scaled_y_train)
    x_lstm_val, y_lstm_val = make_sequences(scaled_x_val, scaled_y_val)
    x_lstm_test, y_lstm_test = make_sequences(scaled_x_test, scaled_y_test)
    
    # --- 2. XGBoost Data Setup (Raw) ---
    # Construct unscaled sequences
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
    
    # Flatten sequences for 2D XGBoost regressor
    x_xgb_train = x_xgb_train_seq.reshape(x_xgb_train_seq.shape[0], -1)
    x_xgb_val = x_xgb_val_seq.reshape(x_xgb_val_seq.shape[0], -1)
    x_xgb_test = x_xgb_test_seq.reshape(x_xgb_test_seq.shape[0], -1)
    
    # Extract actual raw target Close prices and return values for evaluation
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
    """Trains a stronger stacked LSTM model using the validation set for early stopping."""
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
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    )
    
    model.fit(
        x_train, y_train,
        epochs=30,
        batch_size=32,
        validation_data=(x_val, y_val),
        callbacks=[early_stopping],
        verbose=0
    )
    return model

def evaluate_predictions(y_pred, data, name, is_scaled=True):
    """Calculates performance metrics on actual Close price level of the unseen test set."""
    eval_subset = data["eval_df"].copy()
    
    # Inverse scale predicted daily return if scaled, else keep raw
    if is_scaled:
        scaler_y = data["scaler_y"]
        y_pred_returns = scaler_y.inverse_transform(y_pred.reshape(-1, 1)).flatten()
    else:
        y_pred_returns = y_pred
    
    # Align lengths
    n_samples = min(len(y_pred_returns), len(eval_subset))
    y_pred_returns = y_pred_returns[:n_samples]
    eval_subset = eval_subset.iloc[:n_samples].copy()
    
    # Calculate predicted Close prices
    prev_close_val = data["prev_close_val"]
    prev_closes = eval_subset["Close"].shift(1).fillna(prev_close_val).values
    
    actual_closes = eval_subset["Close"].values
    predicted_closes = prev_closes * (1 + y_pred_returns)
    
    # Metrics
    rmse = np.sqrt(np.mean((actual_closes - predicted_closes) ** 2))
    mape = np.mean(np.abs((actual_closes - predicted_closes) / actual_closes)) * 100
    
    # Directional Accuracy (sign check)
    actual_returns = eval_subset["Daily_Return"].values
    correct_direction = np.sign(actual_returns) == np.sign(y_pred_returns)
    directional_accuracy = np.mean(correct_direction) * 100
    
    print(f"\n=========================================")
    print(f" Evaluation Metrics on Test Set: {name}")
    print(f"=========================================")
    print(f"Close Price RMSE: ${rmse:.2f}")
    print(f"Close Price MAPE: {mape:.4f}%")
    print(f"Directional Accuracy: {directional_accuracy:.2f}%")
    
    return {
        "rmse": rmse,
        "mape": mape,
        "directional_accuracy": directional_accuracy
    }

if __name__ == "__main__":
    symbol = "BTC-USD"
    print(f"Fetching market data for {symbol}...")
    df, _, _, _ = fetch_market_data(symbol, "1d")
    
    print(f"Total rows fetched: {len(df)}")
    print("Preparing chronological Train (70%), Val (15%), and Test (15%) splits...")
    data = prepare_data_splits(df)
    
    # 1. XGBoost Model (Tuned Hyperparameters, Raw Data)
    print("\nTraining XGBoost Regressor on RAW Data with Early Stopping...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=500,
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
    
    start_time = time.time()
    xgb_model.fit(
        data["x_xgb_train"], data["y_xgb_train"],
        eval_set=[(data["x_xgb_val"], data["y_xgb_val"])],
        verbose=False
    )
    xgb_train_time = time.time() - start_time
    print(f"XGBoost training completed in {xgb_train_time:.4f} seconds.")
    
    print("Predicting with XGBoost on Test Set (using raw data)...")
    y_pred_xgb = xgb_model.predict(data["x_xgb_test"])
    xgb_metrics = evaluate_predictions(y_pred_xgb, data, "XGBoost", is_scaled=False)
    
    # Print Feature Importances (aggregated over 60 lags)
    feature_names = []
    for lag in range(60, 0, -1):
        for f in FEATURES:
            feature_names.append(f"{f}_lag_{lag}")
    
    importances = xgb_model.feature_importances_
    feature_agg = {f: 0.0 for f in FEATURES}
    for name, imp in zip(feature_names, importances):
        base_feature = name.split("_lag_")[0]
        feature_agg[base_feature] += imp
        
    sorted_agg = sorted(feature_agg.items(), key=lambda x: x[1], reverse=True)
    print("\n=== XGBoost Feature Importances (Aggregated over 60 lags) ===")
    for f, imp in sorted_agg[:10]:
        print(f"{f:<15}: {imp:.4f}")
        
    # 2. LSTM Model (Stacked LSTM on Scaled Data)
    print("\nTraining Stacked LSTM Model on MinMaxScaler Scaled Data...")
    start_time = time.time()
    lstm_model = train_lstm_model_with_val(
        data["x_lstm_train"], 
        data["y_lstm_train"],
        data["x_lstm_val"],
        data["y_lstm_val"],
        seq_length=60
    )
    lstm_train_time = time.time() - start_time
    print(f"LSTM training completed in {lstm_train_time:.4f} seconds.")
    
    print("Predicting with LSTM on Test Set...")
    y_pred_lstm = lstm_model.predict(data["x_lstm_test"]).flatten()
    lstm_metrics = evaluate_predictions(y_pred_lstm, data, "LSTM", is_scaled=True)
    
    # 3. Final Summary Table
    print("\n\n" + "="*50)
    print("      FINAL COMPARISON: XGBoost vs LSTM")
    print("      (Evaluated on chronologically unseen 15% Test Set)")
    print("="*50)
    print(f"{'Metric':<25} | {'XGBoost':<10} | {'LSTM':<10}")
    print("-"*50)
    print(f"{'Training Time (sec)':<25} | {xgb_train_time:<10.2f} | {lstm_train_time:<10.2f}")
    print(f"{'Close Price RMSE ($)':<25} | {xgb_metrics['rmse']:<10.2f} | {lstm_metrics['rmse']:<10.2f}")
    print(f"{'Close Price MAPE (%)':<25} | {xgb_metrics['mape']:<10.4f} | {lstm_metrics['mape']:<10.4f}")
    print(f"{'Directional Acc. (%)':<25} | {xgb_metrics['directional_accuracy']:<10.2f} | {lstm_metrics['directional_accuracy']:<10.2f}")
    print("="*50)
