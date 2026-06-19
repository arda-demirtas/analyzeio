import os
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from typing import Tuple, Dict, Any, List

from backend.config import MODEL_CACHE_DIR, DEFAULT_SEQUENCE_LENGTH

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculates the Relative Strength Index (RSI) for a price series."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Use standard Exponential Moving Average for RSI
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculates the MACD Line, Signal Line, and MACD Histogram."""
    fast_ema = prices.ewm(span=fast, adjust=False).mean()
    slow_ema = prices.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def fetch_market_data(symbol: str, years: int = 3) -> Tuple[pd.DataFrame, str]:
    """
    Downloads historical market data using yfinance, calculates RSI/MACD,
    and returns a cleaned DataFrame and the asset long name.
    """
    ticker = yf.Ticker(symbol)
    
    # Fetch details
    info = ticker.info
    asset_name = info.get("longName") or info.get("shortName") or symbol
    
    # Download daily historical data
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=years * 365)
    
    df = ticker.history(start=start_date, end=end_date, interval="1d")
    
    if df.empty:
        raise ValueError(f"No historical data found for symbol: {symbol}")
        
    # Calculate indicators
    df["RSI"] = calculate_rsi(df["Close"])
    macd_line, signal_line, macd_hist = calculate_macd(df["Close"])
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = macd_hist
    
    # Drop rows with NaN values resulting from indicators (first ~26 rows)
    df = df.dropna(subset=["RSI", "MACD", "MACD_Signal", "MACD_Hist"])
    
    return df, asset_name

def prepare_lstm_data(df: pd.DataFrame, seq_length: int) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler, MinMaxScaler]:
    """
    Scales the data and creates sequences for LSTM training.
    Features: RSI, MACD, Open, Close, Volume
    Target: Close
    """
    features = ["RSI", "MACD", "Open", "Close", "Volume"]
    feature_data = df[features].values
    target_data = df[["Close"]].values
    
    # Normalize features and target separately
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    
    scaled_x = scaler_x.fit_transform(feature_data)
    scaled_y = scaler_y.fit_transform(target_data)
    
    x_seq, y_val = [], []
    for i in range(seq_length, len(scaled_x)):
        x_seq.append(scaled_x[i-seq_length:i])
        y_val.append(scaled_y[i])
        
    return np.array(x_seq), np.array(y_val), scaler_x, scaler_y

def train_lstm_model(x_train: np.ndarray, y_train: np.ndarray, seq_length: int) -> tf.keras.Model:
    """Creates and trains an LSTM model."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, 5)),
        tf.keras.layers.LSTM(units=50, return_sequences=False),
        tf.keras.layers.Dense(units=25, activation="relu"),
        tf.keras.layers.Dense(units=1)
    ])
    
    model.compile(optimizer="adam", loss="mean_squared_error")
    # Train model (15 epochs is fast and accurate enough for daily trading patterns)
    model.fit(x_train, y_train, epochs=15, batch_size=32, verbose=0)
    return model

def evaluate_model_performance(
    model: tf.keras.Model, 
    x_test: np.ndarray, 
    y_test: np.ndarray, 
    scaler_y: MinMaxScaler, 
    df_test: pd.DataFrame,
    seq_length: int
) -> Dict[str, Any]:
    """
    Evaluates LSTM predictions on a test set.
    Computes RMSE, MAPE, and Directional Accuracy.
    """
    if len(x_test) == 0:
        return {"rmse": 0.0, "mape": 0.0, "directional_accuracy": 0.0}
        
    scaled_preds = model.predict(x_test, verbose=0)
    preds = scaler_y.inverse_transform(scaled_preds).flatten()
    actuals = scaler_y.inverse_transform(y_test).flatten()
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    
    # Calculate MAPE
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-10))) * 100
    
    # Calculate Directional Accuracy
    # Align dates for actual direction check
    actual_prices = df_test["Close"].values
    
    # We want to check if the predicted direction matches the actual direction compared to the PREVIOUS day's close
    correct_directions = 0
    total_comparisons = len(preds) - 1
    
    for i in range(1, len(preds)):
        # Actual direction: today's actual vs yesterday's actual
        actual_up = actual_prices[seq_length + i] > actual_prices[seq_length + i - 1]
        # Predicted direction: today's prediction vs yesterday's actual
        pred_up = preds[i] > actual_prices[seq_length + i - 1]
        
        if actual_up == pred_up:
            correct_directions += 1
            
    dir_acc = (correct_directions / total_comparisons * 100) if total_comparisons > 0 else 50.0
    
    return {
        "rmse": float(rmse),
        "mape": float(mape),
        "directional_accuracy": float(dir_acc)
    }

def get_prediction(symbol: str, seq_length: int = DEFAULT_SEQUENCE_LENGTH) -> Dict[str, Any]:
    """
    Main function to coordinate market data retrieval, model loading/training,
    and predicting the next close price.
    """
    # 1. Download and clean data
    df, asset_name = fetch_market_data(symbol, years=3)
    
    # Ensure there is enough data
    if len(df) < seq_length + 50:
        raise ValueError(f"Insufficient data for symbol {symbol}. Needed: {seq_length + 50}, Got: {len(df)}")
    
    # 2. Split data into train (80%) and test (20%) for evaluation
    split_idx = int(len(df) * 0.8)
    df_train = df.iloc[:split_idx]
    df_test = df.iloc[split_idx - seq_length:]  # overlap for sequences
    
    x_train, y_train, scaler_x, scaler_y = prepare_lstm_data(df_train, seq_length)
    x_test, y_test, _, _ = prepare_lstm_data(df_test, seq_length)
    
    # 3. Check if cached model exists
    cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_model.keras")
    model_loaded = False
    
    # Check modification time to enforce 24 hour cache
    if os.path.exists(cache_path):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.datetime.now() - mtime < datetime.timedelta(hours=24):
            try:
                model = tf.keras.models.load_model(cache_path)
                model_loaded = True
            except Exception:
                pass  # If load fails, we will re-train
                
    if not model_loaded:
        # Train a new model
        model = train_lstm_model(x_train, y_train, seq_length)
        model.save(cache_path)
        training_status = "Trained new model"
    else:
        training_status = "Loaded cached model (last 24h)"
        
    # 4. Evaluate performance on test set
    metrics = evaluate_model_performance(model, x_test, y_test, scaler_y, df_test, seq_length)
    metrics["training_status"] = training_status
    
    # 5. Predict the next day's price
    # Extract the last sequence (most recent X days) from the full dataset
    last_features = df[["RSI", "MACD", "Open", "Close", "Volume"]].iloc[-seq_length:].values
    scaled_last_features = scaler_x.transform(last_features)
    
    # Shape for prediction: (1, seq_length, 5)
    input_seq = np.array([scaled_last_features])
    scaled_pred = model.predict(input_seq, verbose=0)
    predicted_close = float(scaler_y.inverse_transform(scaled_pred)[0][0])
    
    # Details of the last available day
    last_row = df.iloc[-1]
    last_date_str = last_row.name.strftime("%Y-%m-%d")
    last_close = float(last_row["Close"])
    
    # Calculate prediction date (next trading day)
    # Simple weekday logic
    last_date = last_row.name
    pred_date = last_date + datetime.timedelta(days=1)
    if pred_date.weekday() >= 5: # Sat or Sun
        pred_date += datetime.timedelta(days=2)
    pred_date_str = pred_date.strftime("%Y-%m-%d")
    
    # Percent change between predicted close and last close
    change_percent = ((predicted_close - last_close) / last_close) * 100
    
    # 6. Format recent history for charting (last 100 days)
    history_df = df.tail(100)
    history_list = []
    for idx, row in history_df.iterrows():
        history_list.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": float(row["Open"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
            "rsi": float(row["RSI"]),
            "macd": float(row["MACD"]),
            "macd_signal": float(row["MACD_Signal"]),
            "macd_hist": float(row["MACD_Hist"]),
        })
        
    return {
        "symbol": symbol,
        "name": asset_name,
        "last_date": last_date_str,
        "last_close": last_close,
        "predicted_close": predicted_close,
        "prediction_date": pred_date_str,
        "price_change_percent": change_percent,
        "metrics": metrics,
        "history": history_list
    }
