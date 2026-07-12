import os
import json
import datetime
import pickle
import numpy as np
from typing import Tuple, Dict, Any, Optional
from backend.config import MODEL_CACHE_DIR, FEATURES, AUTO_TRAINED_SYMBOLS
from backend.prediction_engine import train_lr_model, evaluate_lr_performance

def get_lr_prediction(
    symbol: str,
    interval: str,
    df,
    df_train,
    df_test,
    seq_length: int,
    force_retrain: bool,
    is_daemon: bool,
    max_ret: float,
    min_ret: float
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """Runs the Linear Regression flow to predict next close price and return performance metrics."""
    lr_predicted_close = None
    lr_metrics = None
    
    try:
        split_idx_lr = int(len(df) * 0.8)
        df_train_lr = df.iloc[:split_idx_lr]
        
        def make_raw_lr_sequences_bg(x_data, y_data):
            xs, ys = [], []
            for i in range(seq_length, len(x_data)):
                xs.append(x_data[i-seq_length:i])
                ys.append(y_data[i])
            return np.array(xs).reshape(len(xs), -1), np.array(ys)
            
        x_lr_train, y_lr_train = make_raw_lr_sequences_bg(df_train_lr[FEATURES].values, df_train_lr["Daily_Return"].values)
        x_lr_test, y_lr_test = make_raw_lr_sequences_bg(df_test[FEATURES].values, df_test["Daily_Return"].values)
        
        cache_path_lr = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_seq{seq_length}_model_lr.pkl")
        lr_model_loaded = False
        lr_status = "Trained LR model"
        
        if not force_retrain and os.path.exists(cache_path_lr):
            meta_path_lr = cache_path_lr.replace("_lr.pkl", "_lr_meta.json")
            is_cache_valid = False
            if os.path.exists(meta_path_lr):
                try:
                    with open(meta_path_lr, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    last_trained_str = meta_data.get("predicted_candle_start")
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    if last_trained_str and current_predicted_candle and current_predicted_candle <= last_trained_str:
                        is_cache_valid = True
                except Exception:
                    pass
            if is_cache_valid:
                try:
                    with open(cache_path_lr, "rb") as f:
                        model_lr = pickle.load(f)
                    lr_model_loaded = True
                    lr_status = f"Loaded cached LR model ({interval})"
                except Exception:
                    pass
                    
        if not lr_model_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
            if is_auto_trained_asset and not force_retrain and not is_daemon:
                if os.path.exists(cache_path_lr):
                    try:
                        with open(cache_path_lr, "rb") as f:
                            model_lr = pickle.load(f)
                        lr_model_loaded = True
                        lr_status = f"Loaded cached LR model ({interval} - Fallback)"
                    except Exception:
                        pass
                if not lr_model_loaded:
                    raise ValueError(f"LR Model for {symbol} is currently training.")
            else:
                model_lr = train_lr_model(x_lr_train, y_lr_train)
                with open(cache_path_lr, "wb") as f:
                    pickle.dump(model_lr, f)
                lr_status = f"Trained LR model ({interval})"
            try:
                meta_path_lr = cache_path_lr.replace("_lr.pkl", "_lr_meta.json")
                last_candle_start = df.index[-1]
                current_predicted_candle = df.attrs.get("predicted_candle_start")
                with open(meta_path_lr, "w", encoding="utf-8") as f:
                    json.dump({
                        "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "predicted_candle_start": current_predicted_candle
                    }, f)
            except Exception:
                pass
                
        lr_metrics = evaluate_lr_performance(model_lr, x_lr_test, df_test, seq_length)
        lr_metrics["training_status"] = lr_status
        
        last_features_lr = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
        probs_lr = model_lr.predict_proba(last_features_lr)[0]
        lr_predicted_close = float(probs_lr[1])
        
    except Exception as e:
        print(f"Error in Linear Regression flow: {e}")
        
    return lr_predicted_close, lr_metrics
