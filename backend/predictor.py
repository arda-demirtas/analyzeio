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

FEATURES = [
    "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
    "Open", "Close", "Volume", "High", "Low", 
    "BB_Upper", "BB_Lower", "BB_Width",
    "EMA_20", "EMA_50", "ATR", "Daily_Return",
    "Return_3", "Return_7", "Volume_Change"
]

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

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculates the Average True Range (ATR)."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

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

def fetch_market_data(symbol: str, interval: str = "1d") -> Tuple[pd.DataFrame, str, bool, Optional[float]]:
    """
    Downloads historical market data from Yahoo Finance API for a specific interval,
    resamples hourly to 4-hour if requested, computes indicators, and returns a DataFrame.
    """
    if interval == "15m":
        range_param = "60d"
        api_interval = "15m"
    elif interval == "1h":
        range_param = "365d"
        api_interval = "1h"
    elif interval == "4h":
        range_param = "365d"
        api_interval = "1h"  # Resample from hourly
    elif interval == "1d":
        range_param = "5y"
        api_interval = "1d"
    else:
        raise ValueError(f"Unsupported interval: {interval}")

    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_param}&interval={api_interval}"
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
        timestamps = result.get("timestamp", [])
        quote = result["indicators"]["quote"][0]
        meta = result.get("meta", {})
        current_price = meta.get("regularMarketPrice")
        
        if not timestamps:
            raise ValueError(f"No historical data returned for symbol: {symbol}")
            
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

    # Resample to 4H if interval is 4h
    if interval == "4h":
        df = df.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()
        
    # Get asset name from dictionary, fallback to meta or symbol
    asset_name = TICKER_NAMES.get(symbol)
    if not asset_name:
        asset_name = symbol
        
    is_crypto = symbol.endswith("-USD") or meta.get("instrumentType") == "CRYPTOCURRENCY"
    
    # For daily data, exclude today's incomplete candle if market is active
    if interval == "1d":
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
    
    # New Indicators
    df["ATR"] = calculate_atr(df["High"], df["Low"], df["Close"])
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["Close"] + 1e-10)
    df["Daily_Return"] = df["Close"].pct_change()
    df["Return_3"] = df["Close"].pct_change(3)
    df["Return_7"] = df["Close"].pct_change(7)
    df["Volume_Change"] = df["Volume"].pct_change()
    
    # Drop rows with NaN values resulting from indicators
    df = df.dropna(subset=[
        "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
        "BB_Upper", "BB_Lower", "BB_Width", "EMA_20", "EMA_50", "ATR", 
        "Daily_Return", "Return_3", "Return_7", "Volume_Change"
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
    Features: RSI, MACD, MACD_Signal, MACD_Hist, Open, Close, Volume, High, Low, BB_Upper, BB_Lower, BB_Width, EMA_20, EMA_50, ATR, Daily_Return
    Target: Daily_Return
    """
    features = FEATURES
    feature_data = df[features].values
    target_data = df[["Daily_Return"]].values
    
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

def train_lstm_model(x_train: np.ndarray, y_train: np.ndarray, seq_length: int, use_early_stopping: bool = False) -> tf.keras.Model:
    """Creates and trains an LSTM model with Dropout regularization."""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(seq_length, len(FEATURES))),
        tf.keras.layers.LSTM(units=50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(units=25, activation="relu"),
        tf.keras.layers.Dense(units=1)
    ])
    
    model.compile(optimizer="adam", loss="mean_squared_error")
    
    callbacks = []
    if use_early_stopping:
        callbacks.append(tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=7,
            restore_best_weights=True
        ))
        validation_split = 0.1
        epochs = 80
    else:
        validation_split = 0.0
        epochs = 30
        
    model.fit(
        x_train, 
        y_train, 
        epochs=epochs, 
        batch_size=32, 
        validation_split=validation_split, 
        callbacks=callbacks, 
        verbose=0
    )
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
    preds_returns = scaler_y.inverse_transform(scaled_preds).flatten()
    actual_returns = scaler_y.inverse_transform(y_test).flatten()
    
    # Reconstruct absolute close prices from return predictions
    actual_prices = df_test["Close"].values[seq_length:]
    prev_prices = df_test["Close"].values[seq_length-1:-1]
    
    preds = prev_prices * (1 + preds_returns)
    actuals = actual_prices
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    
    # Calculate MAPE
    mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-10))) * 100
    
    # Calculate Directional Accuracy using returns directly
    correct_directions = 0
    total_comparisons = len(preds_returns)
    
    for i in range(total_comparisons):
        actual_up = actual_returns[i] > 0
        pred_up = preds_returns[i] > 0
        if actual_up == pred_up:
            correct_directions += 1
            
    dir_acc = (correct_directions / total_comparisons * 100) if total_comparisons > 0 else 50.0
    
    return {
        "rmse": float(rmse),
        "mape": float(mape),
        "directional_accuracy": float(dir_acc)
    }

def get_fundamental_analysis(symbol: str, name: str) -> Dict[str, Any]:
    """
    Searches the web for recent news regarding the asset, computes headline sentiment,
    and returns a recommendation and list of articles.
    """
    # Use name (e.g. Bitcoin) for search, fallback to symbol
    search_query = name if name else symbol
    
    # Clean up generic suffixes to make the search query more relevant
    search_query = search_query.replace(" USD", "").replace(" Inc.", "").replace(" Corporation", "").replace(" Futures", "")
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_query}&newsCount=6"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    articles = []
    sentiment_score = 0.0
    sentiment_class = "Neutral"
    recommendation = "No recent fundamental news articles could be analyzed for this asset."
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw_news = data.get("news", [])
            
            # Simple financial sentiment dictionary
            pos_words = {
                "surge", "bullish", "growth", "rise", "gain", "profit", "upbeat", "upgrade", 
                "outperform", "soar", "rally", "boost", "positive", "high", "buy", "jump", 
                "climb", "higher", "strong", "recovery", "success", "optimistic", "green", 
                "breakout", "alliance", "partner", "acquire", "expanded", "soaring"
            }
            neg_words = {
                "plunge", "bearish", "decline", "fall", "loss", "drop", "downbeat", "downgrade", 
                "underperform", "plummet", "crash", "slump", "negative", "low", "sell", "sink", 
                "slide", "lower", "weak", "panic", "failure", "pessimistic", "red", "breakdown", 
                "worry", "concern", "fear", "lawsuit", "dispute", "investigation", "chilling"
            }
            
            total_score = 0.0
            valid_articles = 0
            
            for item in raw_news:
                title = item.get("title")
                publisher = item.get("publisher")
                link = item.get("link")
                if not title or not link:
                    continue
                    
                # Clean title for sentiment check
                clean_title = title.lower()
                # Remove common punctuation
                for char in [".", ",", "!", "?", "'", "\"", ":", ";", "(", ")", "-", "_", "$", "%"]:
                    clean_title = clean_title.replace(char, " ")
                
                words = clean_title.split()
                pos_count = sum(1 for w in words if w in pos_words)
                neg_count = sum(1 for w in words if w in neg_words)
                
                # Single headline score
                denom = pos_count + neg_count
                art_score = (pos_count - neg_count) / denom if denom > 0 else 0.0
                
                # Determine article sentiment
                if art_score > 0.0:
                    art_sentiment = "Bullish"
                elif art_score < 0.0:
                    art_sentiment = "Bearish"
                else:
                    art_sentiment = "Neutral"
                    
                articles.append({
                    "title": title,
                    "publisher": publisher if publisher else "Web News",
                    "link": link,
                    "sentiment": art_sentiment
                })
                
                total_score += art_score
                valid_articles += 1
                
            if valid_articles > 0:
                sentiment_score = total_score / valid_articles
                
            # Classify overall sentiment
            if sentiment_score > 0.12:
                sentiment_class = "Bullish"
                recommendation = (
                    f"Fundamental analysis reveals positive market sentiment for {search_query} "
                    f"based on recent news coverage. Positive drivers, earnings reports, or market "
                    f"alliances suggest a favorable short-term outlook. Buying or holding positions "
                    f"is generally recommended."
                )
            elif sentiment_score < -0.12:
                sentiment_class = "Bearish"
                recommendation = (
                    f"Fundamental analysis indicates negative sentiment for {search_query} "
                    f"due to recent adverse news headlines. Potential regulatory concerns, selloffs, "
                    f"or downtrends in the sector advise caution. Accumulating is not recommended; "
                    f"consider tightening stop-losses or reducing exposure."
                )
            else:
                sentiment_class = "Neutral"
                recommendation = (
                    f"Fundamental news indicators are currently balanced or neutral for {search_query}. "
                    f"The news headlines present a mix of positive and cautious metrics. A 'Hold' "
                    f"strategy or combining this with technical indicators is advised for trading decisions."
                )
    except Exception as e:
        print(f"Error fetching news for fundamental analysis: {e}")
        
    return {
        "sentiment_score": sentiment_score,
        "sentiment_class": sentiment_class,
        "recommendation": recommendation,
        "articles": articles
    }

def get_prediction(symbol: str, interval: str = "1d", seq_length: int = DEFAULT_SEQUENCE_LENGTH) -> Dict[str, Any]:
    """
    Main function to coordinate market data retrieval, model loading/training,
    and predicting the next close price for a specific interval (15m, 1h, 4h, 1d).
    """
    # 1. Download and clean data
    df, asset_name, is_crypto, current_price = fetch_market_data(symbol, interval=interval)
    if current_price is None and not df.empty:
        current_price = float(df["Close"].iloc[-1])
    
    # Ensure there is enough data
    if len(df) < seq_length + 50:
        raise ValueError(f"Insufficient data for symbol {symbol} at interval {interval}. Needed: {seq_length + 50}, Got: {len(df)}")
    
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
    
    # 3. Check if cached model exists for this specific interval
    cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model.keras")
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
        # Train base model on 80% split with early stopping
        model = train_lstm_model(x_train, y_train, seq_length, use_early_stopping=True)
        
        # Evaluate on 20% test data to get honest out-of-sample metrics
        metrics = evaluate_model_performance(model, x_test, y_test, scaler_y_train, df_test, seq_length)
        
        # Fine-tune the same model weights on the test data (latest market data)
        x_test_full, y_test_full, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x, scaler_y)
        
        # Train for 20 epochs without validation split to absorb the latest price action
        model.fit(x_test_full, y_test_full, epochs=20, batch_size=32, verbose=0)
        model.save(cache_path)
        training_status = f"Trained & fine-tuned model ({interval} timeframe)"
    else:
        # Use full scalers to scale the test set for evaluation of the loaded model
        x_test_full, y_test_full, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x, scaler_y)
        metrics = evaluate_model_performance(model, x_test_full, y_test_full, scaler_y, df_test, seq_length)
        training_status = f"Loaded cached model ({interval} last 24h)"
        
    metrics["training_status"] = training_status
    
    # 5. Predict the next close price
    last_features = df[FEATURES].iloc[-seq_length:].values
    scaled_last_features = scaler_x.transform(last_features)
    
    # Shape for prediction: (1, seq_length, 16)
    input_seq = np.array([scaled_last_features])
    scaled_pred = model.predict(input_seq, verbose=0)
    predicted_return = float(scaler_y.inverse_transform(scaled_pred)[0][0])
    
    # Details of the last available candle
    last_row = df.iloc[-1]
    last_close = float(last_row["Close"])
    
    # Reconstruct predicted absolute price
    predicted_close = last_close * (1 + predicted_return)
    
    # Calculate expected close time of the predicted candle
    if interval == "1d":
        last_date_str = last_row.name.strftime("%Y-%m-%d")
        now = datetime.datetime.now()
        if is_crypto:
            if now.hour < 3:
                pred_date = now - datetime.timedelta(days=1)
            else:
                pred_date = now
            close_time = pred_date + datetime.timedelta(days=1)
            expected_close_time = f"{close_time.strftime('%Y-%m-%d')} 03:00 (TRT)"
        else:
            if now.weekday() == 5:    # Saturday -> Monday
                pred_date = now + datetime.timedelta(days=2)
            elif now.weekday() == 6:  # Sunday -> Monday
                pred_date = now + datetime.timedelta(days=1)
            else:
                if now.hour >= 23:
                    pred_date = now + datetime.timedelta(days=1)
                    if pred_date.weekday() == 5:
                        pred_date += datetime.timedelta(days=2)
                else:
                    pred_date = now
                    
            if symbol.endswith(".IS"):
                expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} 18:00 (TRT)"
            else:
                expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} 23:00 (TRT)"
        pred_date_str = pred_date.strftime("%Y-%m-%d")
    else:
        last_date_str = last_row.name.strftime("%Y-%m-%d %H:%M")
        if interval == "15m":
            pred_time = last_row.name + datetime.timedelta(minutes=15)
        elif interval == "1h":
            pred_time = last_row.name + datetime.timedelta(hours=1)
        elif interval == "4h":
            pred_time = last_row.name + datetime.timedelta(hours=4)
        pred_date_str = pred_time.strftime("%Y-%m-%d %H:%M")
        expected_close_time = f"{pred_date_str} (TRT)"
        
    change_percent = ((predicted_close - last_close) / last_close) * 100
    
    # Calculate threshold-filtered technical recommendation (0.2% threshold)
    if change_percent > 0.2:
        tech_signal = "STRONG_BUY"
        tech_text = "Model forecasts high-conviction upward momentum (>0.2%). Opening a Long position is recommended."
    elif change_percent < -0.2:
        tech_signal = "STRONG_SELL"
        tech_text = "Model forecasts high-conviction downward momentum (<-0.2%). Opening a Short position or staying in Cash is recommended."
    else:
        tech_signal = "HOLD"
        tech_text = "Model forecasts low-conviction price consolidation (between -0.2% and 0.2%). Staying in Cash (no position) is recommended to filter out market noise."
        
    technical_recommendation = {
        "signal": tech_signal,
        "text": tech_text
    }
    
    # 6. Format recent history for charting (last 100 candles)
    history_df = df.tail(100)
    history_list = []
    for idx, row in history_df.iterrows():
        if interval == "1d":
            date_str = idx.strftime("%Y-%m-%d")
        else:
            date_str = idx.strftime("%Y-%m-%d %H:%M")
            
        history_list.append({
            "date": date_str,
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
        
    fundamental_result = get_fundamental_analysis(symbol, asset_name)
        
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
        "history": history_list,
        "fundamental_analysis": fundamental_result,
        "technical_recommendation": technical_recommendation
    }

def fetch_interval_history(symbol: str, interval: str) -> List[Dict[str, Any]]:
    """
    Downloads historical data from Yahoo Finance for a specific interval,
    calculates all technical indicators, and returns formatted history points.
    """
    if interval == "15m":
        range_param = "5d"
    elif interval == "1h":
        range_param = "30d"
    elif interval == "1d":
        range_param = "3mo"
    else:
        raise ValueError(f"Unsupported interval: {interval}")
        
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_param}&interval={interval}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        raise ValueError(f"Failed to fetch {interval} data from Yahoo Finance: {r.status_code}")
        
    data = r.json()
    result = data["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]
    
    if not timestamps:
        raise ValueError(f"No historical data returned for symbol: {symbol} at interval {interval}")
        
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
    
    if df.empty:
        raise ValueError(f"Empty data after cleaning for symbol: {symbol} at interval {interval}")
        
    # Calculate indicators
    df["RSI"] = calculate_rsi(df["Close"])
    macd_line, signal_line, macd_hist = calculate_macd(df["Close"])
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = macd_hist
    
    sma_20 = df["Close"].rolling(window=20).mean()
    std_20 = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = sma_20 + 2 * std_20
    df["BB_Lower"] = sma_20 - 2 * std_20
    
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    
    df = df.dropna(subset=[
        "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
        "BB_Upper", "BB_Lower", "EMA_20", "EMA_50"
    ])
    
    history_list = []
    for idx, row in df.iterrows():
        if interval == "1d":
            date_str = idx.strftime("%Y-%m-%d")
        else:
            date_str = idx.strftime("%Y-%m-%d %H:%M")
            
        history_list.append({
            "date": date_str,
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
        
    return history_list

