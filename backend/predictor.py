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

from backend.config import MODEL_CACHE_DIR, DEFAULT_SEQUENCE_LENGTH, AUTO_TRAINED_SYMBOLS

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
    "ETH-USDT": "Ethereum USD",
    "UNI7083-USD": "Uniswap USD",
    "THYAO.IS": "Türk Hava Yolları",
    "EREGL.IS": "Ereğli Demir Çelik",
    "GARAN.IS": "Garanti BBVA",
    "KCHOL.IS": "Koç Holding",
    "AKBNK.IS": "Akbank",
    "ASELS.IS": "Aselsan",
    "TUPRS.IS": "Tüpraş",
    "SISE.IS": "Şişecam",
    "TCELL.IS": "Turkcell",
    "BIMAS.IS": "BİM Birleşik Mağazalar"
}

def fetch_binance_data(binance_symbol: str, interval: str) -> pd.DataFrame:
    """
    Fetches historical kline/candlestick data from Binance public API.
    Paginates twice to retrieve up to 2000 candles for robust LSTM training.
    """
    bin_interval = interval
    limit = 1000
    url = "https://api.binance.com/api/v3/klines"
    
    all_klines = []
    end_time = None
    
    for _ in range(2):
        params = {
            "symbol": binance_symbol,
            "interval": bin_interval,
            "limit": limit
        }
        if end_time:
            params["endTime"] = end_time - 1
            
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            break
        klines = r.json()
        if not klines:
            break
        all_klines = klines + all_klines
        end_time = klines[0][0]
        if len(klines) < limit:
            break
            
    if not all_klines:
        raise ValueError(f"No data returned from Binance for {binance_symbol}")
        
    dates = [datetime.datetime.fromtimestamp(k[0] / 1000, datetime.timezone.utc).replace(tzinfo=None) for k in all_klines]
    df = pd.DataFrame({
        "Open": [float(k[1]) for k in all_klines],
        "High": [float(k[2]) for k in all_klines],
        "Low": [float(k[3]) for k in all_klines],
        "Close": [float(k[4]) for k in all_klines],
        "Volume": [float(k[5]) for k in all_klines]
    }, index=dates)
    df.index.name = "Date"
    return df

def fetch_market_data(symbol: str, interval: str = "1d") -> Tuple[pd.DataFrame, str, bool, Optional[float]]:
    """
    Downloads historical market data from Binance (for crypto) or Yahoo Finance API,
    resamples hourly to 4-hour if requested, computes indicators, and returns a DataFrame.
    """
    is_crypto = symbol.endswith("-USD")
    df = None
    current_price = None
    meta = None
    
    if is_crypto:
        binance_symbol = symbol.replace("-USD", "USDT")
        df = fetch_binance_data(binance_symbol, interval)
        if not df.empty:
            current_price = float(df["Close"].iloc[-1])
    else:
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
            # Safely fill missing volume with 0
            df["Volume"] = df["Volume"].fillna(0)
            # Drop rows where core price information is missing
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
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
        
    meta_dict = meta if meta is not None else {}
    is_crypto = symbol.endswith("-USD") or meta_dict.get("instrumentType") == "CRYPTOCURRENCY"
    
    # For daily data, exclude today's incomplete candle if market is active
    if interval == "1d":
        last_row_date_str = df.index[-1].strftime("%Y-%m-%d")
        now_utc = datetime.datetime.utcnow()
        current_hour_utc = now_utc.hour
        
        if is_crypto:
            today_str = now_utc.strftime("%Y-%m-%d")
            # Close at 00:00 UTC. If before 23:00 UTC, exclude active daily candle.
            close_hour_utc = 23
        elif symbol.endswith(".IS"):
            # BIST: Turkey is UTC+3
            today_trt = (now_utc + datetime.timedelta(hours=3)).date()
            today_str = today_trt.strftime("%Y-%m-%d")
            # Close at 15:00 UTC (18:00 TRT). If before 15:00 UTC, exclude active daily candle.
            close_hour_utc = 15
        else:
            # US Markets: Eastern time is UTC-4 (approximate DST, safe for daily rollover checks)
            today_est = (now_utc - datetime.timedelta(hours=4)).date()
            today_str = today_est.strftime("%Y-%m-%d")
            # Close at 20:00 UTC (16:00 EST). If before 20:00 UTC, exclude active daily candle.
            close_hour_utc = 20
            
        if last_row_date_str == today_str:
            if current_hour_utc < close_hour_utc:
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
    df["Volume_Change"] = df["Volume"].pct_change().fillna(0)

    
    # Replace all infinite values (inf, -inf) with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Drop rows with NaN values resulting from indicators
    df = df.dropna(subset=FEATURES)
    
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

def get_fundamental_analysis(symbol: str, name: str, lang: str = "en") -> Dict[str, Any]:
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
    if lang == "tr":
        recommendation = "Bu varlık için yakın zamanda yayınlanmış temel analiz haber makalesi analiz edilemedi."
    elif lang == "de":
        recommendation = "Für diesen Vermögenswert konnten keine aktuellen fundamentalen Nachrichtenartikel analysiert werden."
    elif lang == "ru":
        recommendation = "Не удалось проанализировать недавние фундаментальные новости для этого актива."
    elif lang == "zh":
        recommendation = "无法分析该资产的近期基本面新闻文章。"
    elif lang == "es":
        recommendation = "No se pudieron analizar artículos de noticias fundamentales recientes para este activo."
    
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
                
            # Classify overall sentiment and construct localized recommendations
            if sentiment_score > 0.12:
                sentiment_class = "Bullish"
                if lang == "tr":
                    recommendation = (
                        f"Son haber kapsamına göre {search_query} için temel analiz olumlu piyasa duyarlılığı gösteriyor. "
                        f"Olumlu etkenler, kazanç raporları veya piyasa ortaklıkları kısa vadeli olumlu bir görünüme işaret ediyor. "
                        f"Genellikle alım yapmak veya pozisyonları korumak önerilir."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die Fundamentalanalyse zeigt auf Basis der jüngsten Berichterstattung eine positive Marktstimmung für {search_query}. "
                        f"Positive Treiber, Gewinnberichte oder Marktallianzen deuten auf einen günstigen kurzfristigen Ausblick hin. "
                        f"Kauf oder Halten von Positionen wird generell empfohlen."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальный анализ выявляет позитивные рыночные настроения для {search_query} на основе недавних новостей. "
                        f"Положительные драйверы, отчеты о доходах или рыночные альянсы указывают на благоприятный краткосрочный прогноз. "
                        f"Обычно рекомендуется покупать или удерживать позиции."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"基于近期新闻报道，{search_query} 的基本面分析显示出积极的市场情绪。利好驱动因素、财报业绩或市场合作预示着短期前景良好。一般建议买入或持有仓位。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"El análisis fundamental revela un sentimiento de mercado positivo para {search_query} según la cobertura de noticias reciente. "
                        f"Los factores impulsores positivos, los informes de ganancias o las alianzas de mercado sugieren una perspectiva favorable a corto plazo. "
                        f"Generalmente se recomienda comprar o mantener posiciones."
                    )
                else:
                    recommendation = (
                        f"Fundamental analysis reveals positive market sentiment for {search_query} "
                        f"based on recent news coverage. Positive drivers, earnings reports, or market "
                        f"alliances suggest a favorable short-term outlook. Buying or holding positions "
                        f"is generally recommended."
                    )
            elif sentiment_score < -0.12:
                sentiment_class = "Bearish"
                if lang == "tr":
                    recommendation = (
                        f"Son olumsuz haber başlıkları nedeniyle {search_query} için temel analiz olumsuz duyarlılığa işaret ediyor. "
                        f"Olası düzenleyici endişeler, satışlar veya sektördeki düşüş trendleri temkinli olmayı gerektiriyor. "
                        f"Alım yapılması önerilmez; zarar durdurma seviyelerini daraltmayı veya maruziyeti azaltmayı düşünebilirsiniz."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die Fundamentalanalyse deutet aufgrund jüngster negativer Schlagzeilen auf eine negative Stimmung für {search_query} hin. "
                        f"Potenzielle regulatorische Bedenken, Ausverkäufe oder Abwärtstrends im Sektor mahnen zur Vorsicht. "
                        f"Ein Nachkauf wird nicht empfohlen; erwägen Sie die Verengung von Stop-Loss-Marken oder die Reduzierung des Risikos."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальный анализ указывает на негативные настроения по {search_query} из-за недавних неблагоприятных новостей. "
                        f"Возможные регуляторные проблемы, распродажи или нисходящие тренды в секторе призывают к осторожности. "
                        f"Накапливать актив не рекомендуется; подумайте о подтягивании стоп-лоссов или снижении рисков."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"由于近期负面新闻，{search_query} 的基本面分析显示出消极情绪。潜在的监管担忧、抛售或行业下行趋势提示需要保持谨慎。不建议加仓；可考虑收紧止损或降低风险敞口。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"El análisis fundamental indica un sentimiento negativo para {search_query} debido a los titulares de noticias adversos recientes. "
                        f"Las posibles preocupaciones regulatorias, las liquidaciones o las tendencias bajistas en el sector aconsejan precaución. "
                        f"No se recomienda acumular; considere ajustar los stop-loss o reducir la exposición."
                    )
                else:
                    recommendation = (
                        f"Fundamental analysis indicates negative sentiment for {search_query} "
                        f"due to recent adverse news headlines. Potential regulatory concerns, selloffs, "
                        f"or downtrends in the sector advise caution. Accumulating is not recommended; "
                        f"consider tightening stop-losses or reducing exposure."
                    )
            else:
                sentiment_class = "Neutral"
                if lang == "tr":
                    recommendation = (
                        f"{search_query} için temel haber göstergeleri şu anda dengeli veya nötr durumda. "
                        f"Haber başlıkları olumlu ve temkinli göstergelerin bir karışımını sunuyor. "
                        f"Ticaret kararları için bir 'Bekle' stratejisi veya bunun teknik göstergelerle birleştirilmesi önerilir."
                    )
                elif lang == "de":
                    recommendation = (
                        f"Die fundamentalen Nachrichtenindikatoren sind für {search_query} derzeit ausgeglichen oder neutral. "
                        f"Die Schlagzeilen präsentieren eine Mischung aus positiven und vorsichtigen Kennzahlen. "
                        f"Für Handelsentscheidungen wird eine 'Halten'-Strategie oder die Kombination mit technischen Indikatoren empfohlen."
                    )
                elif lang == "ru":
                    recommendation = (
                        f"Фундаментальные новостные индикаторы по {search_query} в настоящее время сбалансированы или нейтральны. "
                        f"Заголовки новостей представляют собой смесь положительных и осторожных показателей. "
                        f"Для торговых решений рекомендуется стратегия 'Удерживать' или сочетание этого с техническими индикаторами."
                    )
                elif lang == "zh":
                    recommendation = (
                        f"目前 {search_query} 的基本面新闻指标处于均衡或中性状态。新闻头条呈现出利好与谨慎指标的交织。建议采取“观望/持有”策略，或结合技术指标进行交易决策。"
                    )
                elif lang == "es":
                    recommendation = (
                        f"Los indicadores de noticias fundamentales son actualmente equilibrados o neutrales para {search_query}. "
                        f"Los titulares de las noticias presentan una mezcla de métricas positivas y cautelosas. "
                        f"Se aconseja una estrategia de 'Mantener' o combinar esto con indicadores técnicos para las decisiones operativas."
                    )
                else:
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

def get_prediction(symbol: str, interval: str = "1d", seq_length: int = DEFAULT_SEQUENCE_LENGTH, lang: str = "en", force_retrain: bool = False) -> Dict[str, Any]:
    """
    Main function to coordinate market data retrieval, model loading/training,
    and predicting the next close price for a specific interval (15m, 1h, 4h, 1d).
    """
    # 1. Download and clean data
    df, asset_name, is_crypto, current_price = fetch_market_data(symbol, interval=interval)
    if current_price is None and not df.empty:
        current_price = float(df["Close"].iloc[-1])

    # For daily intervals, ensure the last row matches the expected last completed day's date
    is_pending_data = False
    pending_error_msg = None
    if interval == "1d" and not df.empty:
        now_utc = datetime.datetime.utcnow()
        if is_crypto:
            # Expected last completed daily candle date is yesterday (UTC)
            expected_last_date = now_utc.date() - datetime.timedelta(days=1)
        else:
            # Expected last completed daily candle date is today (if past market close) or yesterday/previous weekday (if before market close)
            if symbol.endswith(".IS"):
                close_hour_utc = 15  # BIST closes at 18:00 TRT (15:00 UTC)
            else:
                close_hour_utc = 20  # US markets close at 16:00 EST (20:00 UTC)

            if now_utc.hour >= close_hour_utc:
                target_completed_date = now_utc.date()
            else:
                target_completed_date = now_utc.date() - datetime.timedelta(days=1)

            while target_completed_date.weekday() in [5, 6]:
                target_completed_date -= datetime.timedelta(days=1)
            expected_last_date = target_completed_date

        # Check the date of the last valid row in cleaned data
        last_row_date = df.index[-1].date()
        if last_row_date < expected_last_date:
            is_pending_data = True
            lang_msg = {
                "tr": f"{symbol} için en son kapanış verisi ({expected_last_date.strftime('%Y-%m-%d')}) henüz Yahoo Finance sunucularında mevcut değil. Tahmin beklemede.",
                "en": f"Latest completed daily data for {symbol} ({expected_last_date.strftime('%Y-%m-%d')}) is not yet available on Yahoo Finance. Prediction is pending."
            }
            pending_error_msg = lang_msg.get(lang, lang_msg["en"])

    predicted_close = None
    change_percent = None
    metrics = None
    training_status = ""

    if not is_pending_data:
        # 2. Split data into train (80%) and test (20%) for evaluation
        split_idx = int(len(df) * 0.8)
        df_train = df.iloc[:split_idx]
        df_test = df.iloc[split_idx - seq_length:]  # overlap for sequences needed to build sequences

        # Fit scalers ONLY on train data — test data must never influence the scaler
        x_train, y_train, scaler_x_train, scaler_y_train = prepare_lstm_data(df_train, seq_length)
        # Scale test data using the train scalers (no fit, only transform — no data leakage)
        x_test, y_test, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x_train, scaler_y_train)

        # 3. Check if cached model exists for this specific interval
        cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model.keras")
        model_loaded = False

        # Check if cached model exists and is up to date relative to the latest completed candle start
        if not force_retrain and os.path.exists(cache_path):
            meta_path = cache_path.replace(".keras", "_meta.json")
            is_cache_valid = False

            if os.path.exists(meta_path):
                try:
                    import json
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    
                    last_trained_str = meta_data.get("last_candle_start")
                    if last_trained_str:
                        last_trained_candle_start = datetime.datetime.strptime(last_trained_str, "%Y-%m-%d %H:%M:%S")
                        last_candle_start = df.index[-1]
                        
                        # Cache is valid if the last completed candle start is NOT newer than the trained one
                        if last_candle_start <= last_trained_candle_start:
                            is_cache_valid = True
                except Exception as meta_err:
                    print(f"Error reading model metadata: {meta_err}")

            if is_cache_valid:
                try:
                    model = tf.keras.models.load_model(cache_path)
                    model_loaded = True
                    training_status = f"Loaded cached model ({interval} - fully up-to-date)"
                except Exception:
                    pass  # If load fails, we will re-train

        if not model_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")

            if is_auto_trained_asset and not force_retrain:
                # Standard user request: do NOT train on the fly. Try loading stale/older cached model
                if os.path.exists(cache_path):
                    try:
                        model = tf.keras.models.load_model(cache_path)
                        model_loaded = True
                        training_status = f"Loaded cached model ({interval} - Stale/Fallback)"
                    except Exception:
                        pass

                # If still not loaded (e.g. no cache file exists yet), raise error
                if not model_loaded:
                    raise ValueError(f"Model for {symbol} is currently being initialized/trained on the server. Please try again in a few minutes.")
            else:
                # Train model ONLY on the 80% train split — test data is never used for training
                model = train_lstm_model(x_train, y_train, seq_length, use_early_stopping=True)

                # Evaluate on the held-out 20% test data (out-of-sample, read-only — no fine-tuning)
                metrics = evaluate_model_performance(model, x_test, y_test, scaler_y_train, df_test, seq_length)

                # Save the model trained purely on train data
                model.save(cache_path)
                training_status = f"Trained model on 80% train data ({interval} timeframe)"

                # Save model metadata containing the start time of the last completed candle
                try:
                    import json
                    meta_path = cache_path.replace(".keras", "_meta.json")
                    last_candle_start = df.index[-1]
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S")
                        }, f)
                except Exception as meta_err:
                    print(f"Error saving model metadata for {symbol}: {meta_err}")

        # If the model was loaded (either cache hit or stale fallback), run evaluation on test set
        if model_loaded:
            # Evaluate using train scalers (consistent with how the model was originally trained)
            metrics = evaluate_model_performance(model, x_test, y_test, scaler_y_train, df_test, seq_length)

        metrics["training_status"] = training_status

        # 5. Predict the next close price using the last seq_length candles
        # Scale using train scaler — this is correct because the model was trained with those scale parameters
        last_features = df[FEATURES].iloc[-seq_length:].values
        scaled_last_features = scaler_x_train.transform(last_features)

        # Shape for prediction: (1, seq_length, num_features)
        input_seq = np.array([scaled_last_features])
        scaled_pred = model.predict(input_seq, verbose=0)
        predicted_return = float(scaler_y_train.inverse_transform(scaled_pred)[0][0])

        # Sanity check: limit predicted daily return to realistic bounds to filter out data outliers
        max_ret = 0.15 if is_crypto else 0.08
        min_ret = -0.15 if is_crypto else -0.08
        if predicted_return > max_ret:
            predicted_return = max_ret
        elif predicted_return < min_ret:
            predicted_return = min_ret

    # Details of the last available candle
    last_row = df.iloc[-1]
    last_close = float(last_row["Close"])

    if not is_pending_data:
        # Reconstruct predicted absolute price
        predicted_close = last_close * (1 + predicted_return)

    
    # Calculate expected close time of the predicted candle using UTC explicitly
    if interval == "1d":
        last_date_str = last_row.name.strftime("%Y-%m-%d")
        now_utc = datetime.datetime.utcnow()
        if is_crypto:
            # Daily crypto candle closes at 00:00 UTC
            pred_date = now_utc.date()
            close_time = datetime.datetime.combine(pred_date, datetime.time.min) + datetime.timedelta(days=1)
            expected_close_time = f"{close_time.strftime('%Y-%m-%d')} 03:00 (TRT)"
        else:
            # Determine close hour in UTC
            if symbol.endswith(".IS"):
                close_hour_utc = 15  # BIST closes at 18:00 TRT (15:00 UTC)
                close_time_str = "18:00 (TRT)"
            else:
                close_hour_utc = 20  # US markets close at 16:00 EST (20:00 UTC)
                close_time_str = "23:00 (TRT)"

            # If current UTC hour is past market close, target is the next day
            if now_utc.hour >= close_hour_utc:
                pred_date = now_utc.date() + datetime.timedelta(days=1)
            else:
                pred_date = now_utc.date()

            # Skip weekends (Saturday=5, Sunday=6)
            while pred_date.weekday() in [5, 6]:
                pred_date += datetime.timedelta(days=1)

            expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} {close_time_str}"

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
        
    if not is_pending_data:
        change_percent = ((predicted_close - last_close) / last_close) * 100
    else:
        change_percent = None
    
    # Calculate threshold-filtered technical recommendation (0.2% threshold)
    if is_pending_data:
        tech_signal = "HOLD"
        if lang == "tr":
            tech_text = "Veri eksikliği nedeniyle işlem tavsiyesi beklemede. Yeni günlük mum kapanışı bekleniyor."
        elif lang == "de":
            tech_text = "Handelsempfehlung steht wegen fehlender Daten aus. Warten auf den neuen Tagesschluss."
        elif lang == "ru":
            tech_text = "Торговая рекомендация отложена из-за отсутствия данных. Ожидание нового дневного закрытия."
        elif lang == "zh":
            tech_text = "由于数据缺失，交易建议待定。等待新的日线收盘。"
        elif lang == "es":
            tech_text = "Recomendación comercial pendiente por falta de datos. Esperando el nuevo cierre diario."
        else:
            tech_text = "Trading recommendation is pending due to missing data. Waiting for the new daily candle close."
    elif change_percent > 0.2:
        tech_signal = "STRONG_BUY"
        if lang == "tr":
            tech_text = "Model, yüksek güvenilirlikli yukarı yönlü ivme öngörüyor (>0.2%). Long (Alış) pozisyonu açılması önerilir."
        elif lang == "de":
            tech_text = "Das Modell prognostiziert eine hohe Aufwärtsdynamik (>0.2%). Die Eröffnung einer Long-Position wird empfohlen."
        elif lang == "ru":
            tech_text = "Модель прогнозирует восходящий импульс высокой степени надежности (>0.2%). Рекомендуется открыть позицию Long."
        elif lang == "zh":
            tech_text = "模型预测高置信度上行趋势 (>0.2%)。建议开立多单（做多）。"
        elif lang == "es":
            tech_text = "El modelo pronostica un impulso alcista de alta convicción (>0.2%). Se recomienda abrir una posición Long."
        else:
            tech_text = "Model forecasts high-conviction upward momentum (>0.2%). Opening a Long position is recommended."
    elif change_percent < -0.2:
        tech_signal = "STRONG_SELL"
        if lang == "tr":
            tech_text = "Model, yüksek güvenilirlikli aşağı yönlü ivme öngörüyor (<-0.2%). Short (Satış) pozisyonu açılması veya Nakitte kalınması önerilir."
        elif lang == "de":
            tech_text = "Das Modell prognostiziert eine hohe Abwärtsdynamik (<-0.2%). Die Eröffnung einer Short-Position oder das Verbleiben in bar wird empfohlen."
        elif lang == "ru":
            tech_text = "Модель прогнозирует нисходящий импульс высокой степени надежности (<-0.2%). Рекомендуется открыть позицию Short или оставаться в кэше."
        elif lang == "zh":
            tech_text = "模型预测高置信度下行趋势 (<-0.2%)。建议开立空单（做空）或持有现金。"
        elif lang == "es":
            tech_text = "El modelo pronostica un impulso bajista de alta convicción (<-0.2%). Se recomienda abrir una posición Short o permanecer en Efectivo."
        else:
            tech_text = "Model forecasts high-conviction downward momentum (<-0.2%). Opening a Short position or staying in Cash is recommended."
    else:
        tech_signal = "HOLD"
        if lang == "tr":
            tech_text = "Model, düşük güvenilirlikli fiyat konsolidasyonu öngörüyor (-0.2% ile 0.2% arasında). Piyasa gürültüsünü filtrelemek için Nakitte kalınması (pozisyon açılmaması) önerilir."
        elif lang == "de":
            tech_text = "Das Modell prognostiziert eine geringe Preiskonsolidierung (zwischen -0.2% und 0.2%). Das Verbleiben in bar (keine Position) wird empfohlen, um Marktstörungen herauszufiltern."
        elif lang == "ru":
            tech_text = "Модель прогнозирует консолидацию цены с низкой степенью надежности (между -0.2% и 0.2%). Рекомендуется оставаться в кэше (без позиций) для фильтрации рыночного шума."
        elif lang == "zh":
            tech_text = "模型预测低置信度震荡整理（在 -0.2% 至 0.2% 之间）。建议持有现金（不建仓）以过滤市场噪音。"
        elif lang == "es":
            tech_text = "El modelo pronostica una consolidación de precios de baja convicción (entre -0.2% y 0.2%). Se recomienda permanecer en Efectivo (sin posición) para filtrar el ruido del mercado."
        else:
            tech_text = "Model forecasts low-conviction price consolidation (between -0.2% and 0.2%). Staying in Cash (no position) is recommended to filter out market noise."
        
    technical_recommendation = {
        "signal": tech_signal,
        "text": tech_text
    }
    
    chart_limit = 730
    history_df = df.tail(chart_limit)
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
        
    fundamental_result = get_fundamental_analysis(symbol, asset_name, lang=lang)
    
    # 7. Log Prediction and resolve past pending predictions in database
    from backend.database import SessionLocal
    from backend.models import PredictionLog
    
    db_session = SessionLocal()
    try:
        # A. Check and update any pending past predictions for this symbol & interval
        pending_logs = (
            db_session.query(PredictionLog)
            .filter(PredictionLog.symbol == symbol, PredictionLog.interval == interval, PredictionLog.actual_close == None)
            .all()
        )
        if pending_logs:
            price_map = {}
            for idx, row in df.iterrows():
                if interval == "1d":
                    d_str = idx.strftime("%Y-%m-%d")
                else:
                    d_str = idx.strftime("%Y-%m-%d %H:%M")
                price_map[d_str] = float(row["Close"])
                
            updated = False
            for pl in pending_logs:
                if pl.prediction_date in price_map:
                    pl.actual_close = price_map[pl.prediction_date]
                    updated = True
            if updated:
                db_session.commit()
                
        # B. Save or update the active prediction log to avoid duplicates on the same target candle date
        if not is_pending_data:
            existing_log = (
                db_session.query(PredictionLog)
                .filter(
                    PredictionLog.symbol == symbol,
                    PredictionLog.interval == interval,
                    PredictionLog.prediction_date == pred_date_str
                )
                .first()
            )
            if existing_log:
                existing_log.predicted_close = predicted_close
                existing_log.last_close = last_close
                existing_log.created_at = datetime.datetime.utcnow()
            else:
                new_log = PredictionLog(
                    symbol=symbol,
                    interval=interval,
                    prediction_date=pred_date_str,
                    predicted_close=predicted_close,
                    last_close=last_close,
                    actual_close=None
                )
                db_session.add(new_log)
            db_session.commit()
    except Exception as db_err:
        print(f"Database logging error in get_prediction: {db_err}")
    finally:
        db_session.close()
        
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
        "technical_recommendation": technical_recommendation,
        "prediction_status": "pending_data" if is_pending_data else "success",
        "prediction_error": pending_error_msg
    }

def fetch_interval_history(symbol: str, interval: str) -> List[Dict[str, Any]]:
    """
    Downloads historical data from Yahoo Finance for a specific interval,
    calculates all technical indicators, and returns formatted history points.
    """
    df, asset_name, is_crypto, current_price = fetch_market_data(symbol, interval=interval)
    
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
    
    chart_limit = 730
    df = df.tail(chart_limit)
    
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


def update_screener_cache(symbol: str, db) -> None:
    """Computes and updates the MarketScreener entry for a given symbol."""
    from backend.models import MarketScreener, PredictionLog
    import datetime

    symbol_upper = symbol.upper().strip()
    try:
        # 1. Get the latest prediction log for daily interval
        log = (
            db.query(PredictionLog)
            .filter(PredictionLog.symbol == symbol_upper, PredictionLog.interval == "1d")
            .order_by(PredictionLog.prediction_date.desc())
            .first()
        )
        
        # 2. Fetch history to compute price, RSI, MACD
        df, _, _, _ = fetch_market_data(symbol_upper, interval="1d")
        if df.empty:
            return
            
        last_row = df.iloc[-1]
        price = float(last_row["Close"])
        rsi = float(last_row["RSI"]) if "RSI" in last_row and not pd.isna(last_row["RSI"]) else 50.0
        
        # MACD Signal
        macd_hist = float(last_row["MACD_Hist"]) if "MACD_Hist" in last_row and not pd.isna(last_row["MACD_Hist"]) else 0.0
        macd_signal = "BULLISH" if macd_hist > 0 else "BEARISH" if macd_hist < 0 else "NEUTRAL"
        
        # Predicted change
        predicted_change = 0.0
        if log:
            predicted_change = ((log.predicted_close - log.last_close) / log.last_close) * 100
            
        name = TICKER_NAMES.get(symbol_upper, symbol_upper)
        
        screener_entry = db.query(MarketScreener).filter(MarketScreener.symbol == symbol_upper).first()
        if screener_entry:
            screener_entry.price = price
            screener_entry.predicted_change = predicted_change
            screener_entry.rsi = rsi
            screener_entry.macd_signal = macd_signal
            screener_entry.name = name
            screener_entry.updated_at = datetime.datetime.utcnow()
        else:
            new_entry = MarketScreener(
                symbol=symbol_upper,
                name=name,
                price=price,
                predicted_change=predicted_change,
                rsi=rsi,
                macd_signal=macd_signal
            )
            db.add(new_entry)
        db.commit()
    except Exception as e:
        print(f"Error updating screener cache for {symbol}: {e}")


def analyze_text_sentiment(title: str, summary: str = "") -> float:
    """
    Calculates a sentiment score between -1.0 (very bearish) and 1.0 (very bullish)
    using key financial sentiment words.
    """
    pos_words = {
        "bullish", "growth", "high", "gain", "breakout", "surpass", "profit", 
        "positive", "strong", "rise", "soar", "rally", "jump", "buy", "upward",
        "boğa", "yükseliş", "artış", "kâr", "güçlü", "rekor", "al", "kazanç", "pozitif"
    }
    neg_words = {
        "bearish", "fall", "drop", "loss", "crash", "negative", "weak", "down", 
        "decline", "slide", "plummet", "slump", "sell", "downward", "worry",
        "ayı", "düşüş", "kayıp", "zayıf", "düşük", "sat", "korku", "risk", "negatif"
    }
    
    score = 0.0
    text = (title + " " + summary).lower()
    
    pos_count = sum(1 for w in pos_words if w in text)
    neg_count = sum(1 for w in neg_words if w in text)
    
    total = pos_count + neg_count
    if total > 0:
        score = (pos_count - neg_count) / total
    return score


def fetch_symbol_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Queries Yahoo Finance Search API to retrieve news articles for the symbol,
    and runs NLP sentiment analysis on each article.
    """
    symbol_upper = symbol.upper().strip()
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol_upper}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    articles = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            raw_news = data.get("news", [])
            for item in raw_news:
                title = item.get("title", "")
                publisher = item.get("publisher", "Yahoo Finance")
                link = item.get("link", "")
                pub_time = item.get("providerPublishTime", 0)
                
                # Perform sentiment analysis
                score = analyze_text_sentiment(title)
                
                # Determine rating text and color badge
                if score >= 0.1:
                    rating = "BULLISH"
                elif score <= -0.1:
                    rating = "BEARISH"
                else:
                    rating = "NEUTRAL"
                    
                articles.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "time": pub_time,
                    "score": score,
                    "rating": rating
                })
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        
    return articles

