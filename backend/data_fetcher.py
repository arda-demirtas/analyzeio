import requests
import datetime
import time
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

from backend.config import TICKER_NAMES, FEATURES
from backend.indicators import (
    calculate_rsi, calculate_macd, calculate_atr,
    calculate_stoch_rsi, calculate_obv, calculate_cci, calculate_williams_r
)

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

        hosts = ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        success = False
        last_error = None
        
        for host in hosts:
            url = f"https://{host}/v8/finance/chart/{symbol}?range={range_param}&interval={api_interval}"
            for attempt in range(3):
                try:
                    r = requests.get(url, headers=headers, timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        result = data["chart"]["result"][0]
                        timestamps = result.get("timestamp", [])
                        quote = result["indicators"]["quote"][0]
                        meta = result.get("meta", {})
                        current_price = meta.get("regularMarketPrice")
                        
                        if timestamps:
                            dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
                            df = pd.DataFrame({
                                "Open": quote["open"],
                                "High": quote["high"],
                                "Low": quote["low"],
                                "Close": quote["close"],
                                "Volume": quote["volume"]
                            }, index=dates)
                            df.index.name = "Date"
                            df["Volume"] = df["Volume"].fillna(0)
                            df = df.dropna(subset=["Open", "High", "Low", "Close"])
                            success = True
                            break
                        else:
                            raise ValueError(f"No historical data returned for symbol: {symbol}")
                    elif r.status_code == 404:
                        raise ValueError(f"Symbol not found (404): {symbol}")
                    else:
                        raise ValueError(f"Failed to fetch data from Yahoo Finance ({host}): HTTP {r.status_code}")
                except Exception as e:
                    last_error = e
                    if "Symbol not found (404)" in str(e):
                        break
                    time.sleep(0.5 * (attempt + 1))
            if success:
                break
                
        if not success:
            raise ValueError(f"No historical data found or failed to parse for symbol: {symbol}. Error: {last_error}")
            
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
    
    # predicted_candle_start will be set on the final dataframe to avoid losing it during slicing/dropna

    # For daily data, exclude today's incomplete candle if market is active
    has_today_candle = False
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
            has_today_candle = True
            if current_hour_utc < close_hour_utc:
                df = df.iloc[:-1]
                
    df.attrs["has_today_candle"] = has_today_candle
        
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
    df["ATR_Percent"] = df["ATR"] / (df["Close"] + 1e-10)
    
    # Calculate StochRSI, OBV, CCI, and Williams %R
    stoch_k, stoch_d = calculate_stoch_rsi(df["RSI"])
    df["Stoch_K"] = stoch_k
    df["Stoch_D"] = stoch_d
    df["OBV"] = calculate_obv(df["Close"], df["Volume"])
    df["CCI"] = calculate_cci(df["High"], df["Low"], df["Close"])
    df["Williams_R"] = calculate_williams_r(df["High"], df["Low"], df["Close"])
    
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["Close"] + 1e-10)
    df["Daily_Return"] = df["Close"].pct_change()
    df["Return_Lag1"] = df["Daily_Return"].shift(1)
    df["Return_Lag3"] = df["Daily_Return"].shift(3)
    df["Return_Lag5"] = df["Daily_Return"].shift(5)
    df["EMA_Diff"] = (df["EMA_20"] - df["EMA_50"]) / (df["EMA_50"] + 1e-10)
    df["BB_Position"] = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"] + 1e-10)

    # Download and merge SPY and VIX macro indicators
    try:
        import yfinance as yf
        macro_df = yf.download(["SPY", "^VIX"], period="5y", interval="1d", progress=False)
        if isinstance(macro_df.columns, pd.MultiIndex):
            macro_df.columns = [f"{col[0]}_{col[1]}" for col in macro_df.columns]
        
        spy_close_col = next((c for c in macro_df.columns if "Close" in c and "SPY" in c), None)
        vix_close_col = next((c for c in macro_df.columns if "Close" in c and "VIX" in c), None)
        
        if spy_close_col and vix_close_col:
            macro_df["SPY_Return_1d"] = macro_df[spy_close_col].pct_change(1)
            macro_df["SPY_Return_5d"] = macro_df[spy_close_col].pct_change(5)
            macro_df["VIX_Close"] = macro_df[vix_close_col]
            
            macro_clean = macro_df[["SPY_Return_1d", "SPY_Return_5d", "VIX_Close"]].copy()
            
            df = df.join(macro_clean, how="left")
            df["SPY_Return_1d"] = df["SPY_Return_1d"].ffill().fillna(0.0)
            df["SPY_Return_5d"] = df["SPY_Return_5d"].ffill().fillna(0.0)
            df["VIX_Close"] = df["VIX_Close"].ffill().fillna(15.0)
        else:
            df["SPY_Return_1d"] = 0.0
            df["SPY_Return_5d"] = 0.0
            df["VIX_Close"] = 15.0
    except Exception as e:
        print(f"Error fetching macro data: {e}")
        df["SPY_Return_1d"] = 0.0
        df["SPY_Return_5d"] = 0.0
        df["VIX_Close"] = 15.0

    # Replace all infinite values (inf, -inf) with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # Drop rows with NaN values resulting from indicators
    df = df.dropna(subset=FEATURES)
    
    # Store the predicted candle start date/time on the final dataframe instance
    if not df.empty:
        if interval == "1d":
            df.attrs["predicted_candle_start"] = df.index[-1].strftime("%Y-%m-%d")
        else:
            df.attrs["predicted_candle_start"] = df.index[-1].strftime("%Y-%m-%d %H:%M")
    
    return df, asset_name, is_crypto, current_price


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
            "atr": float(row["ATR"]) if "ATR" in row and not pd.isna(row["ATR"]) else 0.0,
            "stoch_k": float(row["Stoch_K"]) if "Stoch_K" in row and not pd.isna(row["Stoch_K"]) else 50.0,
            "stoch_d": float(row["Stoch_D"]) if "Stoch_D" in row and not pd.isna(row["Stoch_D"]) else 50.0,
            "obv": float(row["OBV"]) if "OBV" in row and not pd.isna(row["OBV"]) else 0.0,
            "cci": float(row["CCI"]) if "CCI" in row and not pd.isna(row["CCI"]) else 0.0,
            "williams_r": float(row["Williams_R"]) if "Williams_R" in row and not pd.isna(row["Williams_R"]) else -50.0,
        })
        
    return history_list
