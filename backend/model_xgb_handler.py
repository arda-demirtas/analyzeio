import os
import json
import datetime
import numpy as np
import xgboost as xgb
from typing import Tuple, Dict, Any, Optional
from backend.config import MODEL_CACHE_DIR, FEATURES, AUTO_TRAINED_SYMBOLS
from backend.prediction_engine import evaluate_xgb_performance

def get_xgb_prediction(
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
    """Runs the XGBoost model flow to predict next close price and return performance metrics."""
    xgb_predicted_close = None
    xgb_metrics = None
    
    try:
        val_split = int(len(df_train) * 0.85)
        df_train_sub = df_train.iloc[:val_split]
        df_val = df_train.iloc[val_split - seq_length:]
        
        def make_raw_xgb_sequences(x_data, y_data):
            xs, ys = [], []
            for i in range(seq_length, len(x_data)):
                xs.append(x_data[i-seq_length:i])
                ys.append(y_data[i])
            return np.array(xs).reshape(len(xs), -1), np.array(ys)
            
        y_train_dir = (df_train_sub["Daily_Return"].values > 0).astype(int)
        y_val_dir = (df_val["Daily_Return"].values > 0).astype(int)
        y_test_dir = (df_test["Daily_Return"].values > 0).astype(int)

        x_xgb_train, y_xgb_train = make_raw_xgb_sequences(df_train_sub[FEATURES].values, y_train_dir)
        x_xgb_val, y_xgb_val = make_raw_xgb_sequences(df_val[FEATURES].values, y_val_dir)
        x_xgb_test, y_xgb_test = make_raw_xgb_sequences(df_test[FEATURES].values, y_test_dir)
        
        cache_path_xgb = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_seq{seq_length}_model.json")
        xgb_loaded = False
        xgb_status = "Trained XGBoost model"
        
        if not force_retrain and os.path.exists(cache_path_xgb):
            meta_path_xgb = cache_path_xgb.replace(".json", "_meta.json")
            is_cache_valid = False
            if os.path.exists(meta_path_xgb):
                try:
                    with open(meta_path_xgb, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    last_trained_str = meta_data.get("predicted_candle_start")
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    if last_trained_str and current_predicted_candle and current_predicted_candle <= last_trained_str:
                        is_cache_valid = True
                except Exception:
                    pass
            if is_cache_valid:
                try:
                    model_xgb = xgb.XGBClassifier()
                    model_xgb.load_model(cache_path_xgb)
                    xgb_loaded = True
                    xgb_status = f"Loaded cached XGBoost model ({interval})"
                except Exception:
                    pass
        
        if not xgb_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
            if is_auto_trained_asset and not force_retrain and not is_daemon:
                if os.path.exists(cache_path_xgb):
                    try:
                        model_xgb = xgb.XGBClassifier()
                        model_xgb.load_model(cache_path_xgb)
                        xgb_loaded = True
                        xgb_status = f"Loaded cached XGBoost model ({interval} - Fallback)"
                    except Exception:
                        pass
                if not xgb_loaded:
                    raise ValueError(f"XGBoost Model for {symbol} is currently training.")
            else:
                model_xgb = xgb.XGBClassifier(
                    n_estimators=30, max_depth=3, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1,
                    early_stopping_rounds=15, random_state=42, n_jobs=-1, eval_metric="logloss"
                )
                model_xgb.fit(
                    x_xgb_train, y_xgb_train,
                    eval_set=[(x_xgb_val, y_xgb_val)],
                    verbose=False
                )
                model_xgb.save_model(cache_path_xgb)
                xgb_status = f"Trained XGBoost model ({interval})"
                try:
                    meta_path_xgb = cache_path_xgb.replace(".json", "_meta.json")
                    last_candle_start = df.index[-1]
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    with open(meta_path_xgb, "w", encoding="utf-8") as f:
                        json.dump({
                            "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S"),
                            "predicted_candle_start": current_predicted_candle
                        }, f)
                except Exception:
                    pass
        
        xgb_metrics = evaluate_xgb_performance(model_xgb, x_xgb_test, df_test, seq_length)
        xgb_metrics["training_status"] = xgb_status
        
        last_features_xgb = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
        probs_xgb = model_xgb.predict_proba(last_features_xgb)[0]
        xgb_predicted_close = float(probs_xgb[1])
        
    except Exception as e:
        print(f"Error in XGBoost flow: {e}")
        
    return xgb_predicted_close, xgb_metrics

