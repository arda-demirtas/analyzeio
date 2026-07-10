import os
import json
import datetime
import pickle
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional
from backend.config import MODEL_CACHE_DIR, AUTO_TRAINED_SYMBOLS
from backend.prediction_engine import train_lr_model, evaluate_lr_performance

def calculate_sr_features_handler(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Computes daily support and resistance distance features without lookahead bias using vectorized operations."""
    closes = df["Close"].values
    highs = df["High"].values if "High" in df.columns else closes
    lows = df["Low"].values if "Low" in df.columns else closes
    
    dist_to_sup_list = []
    dist_to_res_list = []
    min_history = 30
    
    # Pre-calculate rolling masks for window sizes 5 and 20
    rolling_max_5 = df["High"].rolling(window=2*5 + 1, center=True).max().values
    peaks_5 = (df["High"].values == rolling_max_5)
    rolling_min_5 = df["Low"].rolling(window=2*5 + 1, center=True).min().values
    valleys_5 = (df["Low"].values == rolling_min_5)
    
    rolling_max_20 = df["High"].rolling(window=2*20 + 1, center=True).max().values
    peaks_20 = (df["High"].values == rolling_max_20)
    rolling_min_20 = df["Low"].rolling(window=2*20 + 1, center=True).min().values
    valleys_20 = (df["Low"].values == rolling_min_20)
    
    for i in range(len(df)):
        if i < min_history:
            dist_to_sup_list.append(0.02)
            dist_to_res_list.append(0.02)
            continue
            
        # Determine window size based on historical length (i)
        window_size = 20 if i > 300 else 5
        peaks_mask = peaks_20 if i > 300 else peaks_5
        valleys_mask = valleys_20 if i > 300 else valleys_5
        
        # Max confirmed index k
        max_k = i - window_size - 1
        
        confirmed_peaks = highs[:max_k + 1][peaks_mask[:max_k + 1]]
        confirmed_valleys = lows[:max_k + 1][valleys_mask[:max_k + 1]]
        
        current_price = closes[i]
        supports = sorted(list(set([v for v in confirmed_valleys if v < current_price])), reverse=True)[:5]
        resistances = sorted(list(set([p for p in confirmed_peaks if p > current_price])))[:5]
        
        if not supports or not resistances:
            h = highs[i-1]
            l = lows[i-1]
            c = closes[i-1]
            pivot = (h + l + c) / 3.0
            if not supports:
                supports = [2 * pivot - h]
            if not resistances:
                resistances = [2 * pivot - l]
                
        closest_resistance = min(resistances) if resistances else current_price * 1.02
        closest_support = max(supports) if supports else current_price * 0.98
        
        dist_to_res = (closest_resistance - current_price) / current_price
        dist_to_sup = (current_price - closest_support) / current_price
        
        dist_to_sup_list.append(dist_to_sup)
        dist_to_res_list.append(dist_to_res)
        
    return np.array(dist_to_sup_list), np.array(dist_to_res_list)

def get_sr_prediction(
    symbol: str,
    interval: str,
    df: pd.DataFrame,
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    seq_length: int,
    force_retrain: bool,
    is_daemon: bool,
    max_ret: float,
    min_ret: float
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """Runs the S/R Only model flow to predict next close direction and return performance metrics."""
    sr_predicted_close = None
    sr_metrics = None
    
    try:
        dist_to_sup, dist_to_res = calculate_sr_features_handler(df)
        
        df_clean = df.copy()
        df_clean["Dist_To_Support"] = dist_to_sup
        df_clean["Dist_To_Resistance"] = dist_to_res
        
        split_idx = int(len(df_clean) * 0.8)
        df_train_clean = df_clean.iloc[:split_idx]
        df_test_clean = df_clean.iloc[split_idx - seq_length:]
        
        sr_features = ["Dist_To_Support", "Dist_To_Resistance"]
        
        def make_sequences_local(x_data, y_data):
            xs, ys = [], []
            for i in range(seq_length, len(x_data)):
                xs.append(x_data[i-seq_length:i])
                ys.append(y_data[i])
            return np.array(xs).reshape(len(xs), -1), np.array(ys)
            
        y_train_dir = (df_train_clean["Daily_Return"].values > 0).astype(int)
        y_test_dir = (df_test_clean["Daily_Return"].values > 0).astype(int)
        
        x_sr_train, y_sr_train = make_sequences_local(df_train_clean[sr_features].values, y_train_dir)
        x_sr_test, y_sr_test = make_sequences_local(df_test_clean[sr_features].values, y_test_dir)
        
        cache_path_sr = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model_sr.pkl")
        sr_model_loaded = False
        sr_status = "Trained S/R model"
        
        if not force_retrain and os.path.exists(cache_path_sr):
            meta_path_sr = cache_path_sr.replace("_sr.pkl", "_sr_meta.json")
            is_cache_valid = False
            if os.path.exists(meta_path_sr):
                try:
                    with open(meta_path_sr, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    last_trained_str = meta_data.get("predicted_candle_start")
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    if last_trained_str and current_predicted_candle and current_predicted_candle <= last_trained_str:
                        is_cache_valid = True
                except Exception:
                    pass
            if is_cache_valid:
                try:
                    with open(cache_path_sr, "rb") as f:
                        model_sr = pickle.load(f)
                    sr_model_loaded = True
                    sr_status = f"Loaded cached S/R model ({interval})"
                except Exception:
                    pass
                    
        if not sr_model_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
            if is_auto_trained_asset and not force_retrain and not is_daemon:
                if os.path.exists(cache_path_sr):
                    try:
                        with open(cache_path_sr, "rb") as f:
                            model_sr = pickle.load(f)
                        sr_model_loaded = True
                        sr_status = f"Loaded cached S/R model ({interval} - Fallback)"
                    except Exception:
                        pass
                if not sr_model_loaded:
                    raise ValueError(f"S/R Model for {symbol} is currently training.")
            else:
                model_sr = train_lr_model(x_sr_train, y_sr_train)
                with open(cache_path_sr, "wb") as f:
                    pickle.dump(model_sr, f)
                sr_status = f"Trained S/R model ({interval})"
            try:
                meta_path_sr = cache_path_sr.replace("_sr.pkl", "_sr_meta.json")
                last_candle_start = df.index[-1]
                current_predicted_candle = df.attrs.get("predicted_candle_start")
                with open(meta_path_sr, "w", encoding="utf-8") as f:
                    json.dump({
                        "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "predicted_candle_start": current_predicted_candle
                    }, f)
            except Exception:
                pass
                
        sr_metrics = evaluate_lr_performance(model_sr, x_sr_test, df_test_clean, seq_length)
        sr_metrics["training_status"] = sr_status
        
        last_features_sr = df_clean[sr_features].iloc[-seq_length:].values.flatten().reshape(1, -1)
        probs_sr = model_sr.predict_proba(last_features_sr)[0]
        sr_predicted_close = float(probs_sr[1])
        
    except Exception as e:
        print(f"Error in S/R model flow: {e}")
        
    return sr_predicted_close, sr_metrics
