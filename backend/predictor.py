import os
import sys
import datetime
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from typing import Tuple, Dict, Any, List, Optional

from backend.config import MODEL_CACHE_DIR, DEFAULT_SEQUENCE_LENGTH

FEATURES = ["RSI", "MACD", "Open", "Close", "Volume", "High", "Low", "BB_Upper", "BB_Lower", "EMA_20", "EMA_50"]

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

# Dictionary of popular symbols to their readable names
TICKER_NAMES = {
    "BTC-USD": "Bitcoin USD",
    "ETH-USD": "Ethereum USD",
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla Inc.",
    "GC=F": "Gold Futures",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "BTC-USDT": "Bitcoin USD",
    "ETH-USDT": "Ethereum USD"
}

def fetch_market_data(symbol: str, years: int = 3) -> Tuple[pd.DataFrame, str, bool, Optional[float]]:
    """
    Downloads historical market data directly from Yahoo Finance API using requests with a browser User-Agent
    to bypass datacenter IP blocks, calculates technical indicators, and returns a cleaned DataFrame.
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=years * 365)
    
    period1 = int(start_date.timestamp())
    period2 = int(end_date.timestamp())
    
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval=1d"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    current_price = None
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            raise ValueError(f"Failed to fetch data from Yahoo Finance: {r.status_code}")
            
        data = r.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        meta = result.get("meta", {})
        current_price = meta.get("regularMarketPrice")
        
        # Parse lists
        dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
        df = pd.DataFrame({
            "Open": quote["open"],
            "High": quote["high"],
            "Low": quote["low"],
            "Close": quote["close"],
            "Volume": quote["volume"]
        }, index=dates)
        df.index.name = "Date"
        df = df.dropna()
        
    except Exception as e:
        raise ValueError(f"No historical data found or failed to parse for symbol: {symbol}. Error: {e}")
        
    if df.empty:
        raise ValueError(f"No historical data found for symbol: {symbol}")
        
    # Get asset name from dictionary, fallback to meta or symbol
    asset_name = TICKER_NAMES.get(symbol)
    if not asset_name:
        asset_name = symbol
        
    # Check if cryptocurrency
    is_crypto = symbol.endswith("-USD") or meta.get("instrumentType") == "CRYPTOCURRENCY"
    last_row_date_str = df.index[-1].strftime("%Y-%m-%d")
    
    if is_crypto:
        today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    else:
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    if last_row_date_str == today_str:
        current_hour = datetime.datetime.now().hour
        if is_crypto or current_hour < 23:
            df = df.iloc[:-1]
        
    # Calculate indicators
    df["RSI"] = calculate_rsi(df["Close"])
    macd_line, signal_line, macd_hist = calculate_macd(df["Close"])
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = macd_hist
    
    # Bollinger Bands
    sma_20 = df["Close"].rolling(window=20).mean()
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = sma_20 + 2 * std_20
    df["BB_Lower"] = sma_20 - 2 * std_20
    
    # EMAs
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    
    # Drop rows with NaN values resulting from indicators
    df = df.dropna(subset=[
        "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
        "BB_Upper", "BB_Lower", "EMA_20", "EMA_50"
    ])
    
    return df, asset_name, is_crypto, current_price

def prepare_lstm_data(
    df: pd.DataFrame, 
    seq_length: int, 
    scaler_x: Optional[MinMaxScaler] = None, 
    scaler_y: Optional[MinMaxScaler] = None
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler, MinMaxScaler]:
    """
    Scales the data and creates sequences for LSTM training.
    Features: RSI, MACD, Open, Close, Volume, High, Low, BB_Upper, BB_Lower, EMA_20, EMA_50
    Target: Close
    """
    features = FEATURES
    feature_data = df[features].values
    target_data = df[["Close"]].values
    
    # Normalize features and target separately
    if scaler_x is None:
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaled_x = scaler_x.fit_transform(feature_data)
    else:
        scaled_x = scaler_x.transform(feature_data)
        
    if scaler_y is None:
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        scaled_y = scaler_y.fit_transform(target_data)
    else:
        scaled_y = scaler_y.transform(target_data)
    
    x_seq, y_val = [], []
    for i in range(seq_length, len(scaled_x)):
        x_seq.append(scaled_x[i-seq_length:i])
        y_val.append(scaled_y[i])
        
    return np.array(x_seq), np.array(y_val), scaler_x, scaler_y

def train_lstm_model(x_train: np.ndarray, y_train: np.ndarray, seq_length: int) -> tf.keras.Model:
    """Creates and trains an LSTM model."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
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
    df, asset_name, is_crypto, current_price = fetch_market_data(symbol, years=3)
    if current_price is None and not df.empty:
        current_price = float(df["Close"].iloc[-1])
    
    # Ensure there is enough data
    if len(df) < seq_length + 50:
        raise ValueError(f"Insufficient data for symbol {symbol}. Needed: {seq_length + 50}, Got: {len(df)}")
    
    # 2. Split data into train (80%) and test (20%) for evaluation
    split_idx = int(len(df) * 0.8)
    df_train = df.iloc[:split_idx]
    df_test = df.iloc[split_idx - seq_length:]  # overlap for sequences
    
    # Fit train scalers for evaluation
    x_train, y_train, scaler_x_train, scaler_y_train = prepare_lstm_data(df_train, seq_length)
    # Scale test data using train scalers
    x_test, y_test, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x_train, scaler_y_train)
    
    # Fit full scalers for final prediction
    x_all, y_all, scaler_x, scaler_y = prepare_lstm_data(df, seq_length)
    
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
        # Train temporary model for evaluation
        eval_model = train_lstm_model(x_train, y_train, seq_length)
        metrics = evaluate_model_performance(eval_model, x_test, y_test, scaler_y_train, df_test, seq_length)
        
        # Train final model on 100% of the data
        model = train_lstm_model(x_all, y_all, seq_length)
        model.save(cache_path)
        training_status = "Trained new model (100% historical data)"
    else:
        # Use full scalers to scale the test set for evaluation of the loaded model
        x_test_full, y_test_full, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x, scaler_y)
        metrics = evaluate_model_performance(model, x_test_full, y_test_full, scaler_y, df_test, seq_length)
        training_status = "Loaded cached model (last 24h)"
        
    metrics["training_status"] = training_status
    
    # 5. Predict the next day's price
    # Extract the last sequence (most recent X days) from the full dataset
    last_features = df[FEATURES].iloc[-seq_length:].values
    scaled_last_features = scaler_x.transform(last_features)
    
    # Shape for prediction: (1, seq_length, 11)
    input_seq = np.array([scaled_last_features])
    scaled_pred = model.predict(input_seq, verbose=0)
    predicted_close = float(scaler_y.inverse_transform(scaled_pred)[0][0])
    
    # Details of the last available day
    last_row = df.iloc[-1]
    last_date_str = last_row.name.strftime("%Y-%m-%d")
    last_close = float(last_row["Close"])
    
    # Cryptocurrencies trade 24/7. Other assets (stocks, commodities) skip weekends.

    # Calculate prediction date based on the current local time in Turkey (TRT / UTC+3)
    now = datetime.datetime.now()
    
    if is_crypto:
        # Cryptocurrencies close at 00:00 UTC, which is 03:00 TRT next day.
        # If current local time is before 03:00 AM, the active candle is yesterday's.
        # If after 03:00 AM, the active candle is today's.
        if now.hour < 3:
            pred_date = now - datetime.timedelta(days=1)
        else:
            pred_date = now
            
        close_time = pred_date + datetime.timedelta(days=1)
        expected_close_time = f"{close_time.strftime('%Y-%m-%d')} 03:00 (TRT)"
    else:
        # Stock markets / Commodities
        # Standard US market closes at 23:00 TRT.
        # If now is Saturday or Sunday, the next session is Monday.
        if now.weekday() == 5:    # Saturday -> Monday
            pred_date = now + datetime.timedelta(days=2)
        elif now.weekday() == 6:  # Sunday -> Monday
            pred_date = now + datetime.timedelta(days=1)
        else:
            if now.hour >= 23:
                # Today's session is closed. Next session is tomorrow (or Monday if it's Friday night)
                pred_date = now + datetime.timedelta(days=1)
                if pred_date.weekday() == 5:    # Friday night -> Monday
                    pred_date += datetime.timedelta(days=2)
            else:
                # Today's session is active/upcoming
                pred_date = now
                
        if symbol.endswith(".IS"):
            expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} 18:00 (TRT)"
        else:
            expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} 23:00 (TRT)"
            
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
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "rsi": float(row["RSI"]),
            "macd": float(row["MACD"]),
            "macd_signal": float(row["MACD_Signal"]),
            "macd_hist": float(row["MACD_Hist"]),
            "bb_upper": float(row["BB_Upper"]),
            "bb_lower": float(row["BB_Lower"]),
            "ema_20": float(row["EMA_20"]),
            "ema_50": float(row["EMA_50"]),
        })
        
    return {
        "symbol": symbol,
        "name": asset_name,
        "last_date": last_date_str,
        "last_close": last_close,
        "predicted_close": predicted_close,
        "prediction_date": pred_date_str,
        "expected_close_time": expected_close_time,
        "price_change_percent": change_percent,
        "current_price": current_price,
        "metrics": metrics,
        "history": history_list
    }
