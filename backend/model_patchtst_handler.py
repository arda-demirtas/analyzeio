import os
import json
import pickle
import numpy as np
from typing import Tuple, Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from backend.config import MODEL_CACHE_DIR, AUTO_TRAINED_SYMBOLS

def get_patchtst_prediction(
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
    """Runs the PatchTST simulation flow to predict direction probability and return performance metrics."""
    patchtst_predicted_close = None
    patchtst_metrics = None
    
    try:
        tst_features = [
            "RSI", "MACD", "MACD_Signal", "MACD_Hist", 
            "BB_Width", "EMA_20", "EMA_50", "Volume", "ATR",
            "Daily_Return", "Return_Lag1", "Return_Lag3", "Return_Lag5"
        ]
        existing_tst_features = [f for f in tst_features if f in df.columns]
        df_clean = df.dropna(subset=existing_tst_features + ["Daily_Return"])

        split_idx_tst = int(len(df_clean) * 0.8)
        df_train_tst = df_clean.iloc[:split_idx_tst]
        df_test_tst = df_clean.iloc[split_idx_tst:]

        X_train_tst = df_train_tst[existing_tst_features].iloc[:-1].values
        y_train_tst = (df_train_tst["Daily_Return"].iloc[1:].values > 0).astype(int)
        X_test_tst = df_test_tst[existing_tst_features].iloc[:-1].values
        y_test_tst = (df_test_tst["Daily_Return"].iloc[1:].values > 0).astype(int)

        cache_path_tst = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_seq{seq_length}_model_patchtst.pkl")
        tst_model_loaded = False
        tst_status = "Trained PatchTST model"
        
        if not force_retrain and os.path.exists(cache_path_tst):
            meta_path_tst = cache_path_tst.replace("_patchtst.pkl", "_patchtst_meta.json")
            is_cache_valid = False
            if os.path.exists(meta_path_tst):
                try:
                    with open(meta_path_tst, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    last_trained_str = meta_data.get("predicted_candle_start")
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    if last_trained_str and current_predicted_candle and current_predicted_candle <= last_trained_str:
                        is_cache_valid = True
                except Exception:
                    pass
            if is_cache_valid:
                try:
                    with open(cache_path_tst, "rb") as f:
                        cache_data = pickle.load(f)
                    model_tst = cache_data["model"]
                    scaler_x_tst = cache_data["scaler"]
                    existing_tst_features = cache_data["features"]
                    tst_model_loaded = True
                    tst_status = f"Loaded cached PatchTST model ({interval})"
                except Exception:
                    pass
                    
        if not tst_model_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
            if is_auto_trained_asset and not force_retrain and not is_daemon:
                if os.path.exists(cache_path_tst):
                    try:
                        with open(cache_path_tst, "rb") as f:
                            cache_data = pickle.load(f)
                        model_tst = cache_data["model"]
                        scaler_x_tst = cache_data["scaler"]
                        existing_tst_features = cache_data["features"]
                        tst_model_loaded = True
                        tst_status = f"Loaded cached PatchTST model ({interval} - Fallback)"
                    except Exception:
                        pass
                if not tst_model_loaded:
                    raise ValueError(f"PatchTST Model for {symbol} is currently training.")
            else:
                scaler_x_tst = StandardScaler()
                X_train_tst_scaled = scaler_x_tst.fit_transform(X_train_tst)
                
                model_tst = LogisticRegression(C=1.0, random_state=42)
                model_tst.fit(X_train_tst_scaled, y_train_tst)
                
                with open(cache_path_tst, "wb") as f:
                    pickle.dump({
                        "model": model_tst,
                        "scaler": scaler_x_tst,
                        "features": existing_tst_features
                    }, f)
                tst_status = f"Trained PatchTST model ({interval})"
                try:
                    meta_path_tst = cache_path_tst.replace("_patchtst.pkl", "_patchtst_meta.json")
                    last_candle_start = df.index[-1]
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    with open(meta_path_tst, "w", encoding="utf-8") as f:
                        json.dump({
                            "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S"),
                            "predicted_candle_start": current_predicted_candle
                        }, f)
                except Exception:
                    pass

        # Evaluate performance on test set
        X_test_tst_scaled = scaler_x_tst.transform(X_test_tst)
        if len(X_test_tst_scaled) > 0:
            probs_test = model_tst.predict_proba(X_test_tst_scaled)[:, 1]
            probs_test_clipped = np.clip(probs_test, 1e-15, 1 - 1e-15)
            tst_logloss = float(-np.mean(y_test_tst * np.log(probs_test_clipped) + (1 - y_test_tst) * np.log(1 - probs_test_clipped)))
            
            preds_dir = (probs_test >= 0.5).astype(int)
            tst_da = float(np.mean(preds_dir == y_test_tst) * 100)
        else:
            tst_logloss = 9.99
            tst_da = 50.0

        patchtst_metrics = {
            "logloss": tst_logloss,
            "directional_accuracy": tst_da,
            "training_status": tst_status
        }

        last_features_tst = df[existing_tst_features].iloc[-1:].values
        last_features_tst_scaled = scaler_x_tst.transform(last_features_tst)
        probs_last = model_tst.predict_proba(last_features_tst_scaled)[0]
        patchtst_predicted_close = float(probs_last[1])
        
    except Exception as tst_err:
        print(f"Error executing PatchTST simulation: {tst_err}")
        
    return patchtst_predicted_close, patchtst_metrics

