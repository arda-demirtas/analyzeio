import os
import json
import datetime
import numpy as np
import tensorflow as tf
from typing import Tuple, Dict, Any, Optional
from backend.config import MODEL_CACHE_DIR, FEATURES, AUTO_TRAINED_SYMBOLS
from backend.prediction_engine import prepare_lstm_data, train_lstm_model, evaluate_model_performance

def get_lstm_prediction(
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
    """Runs the LSTM model flow to predict next close price and return performance metrics."""
    lstm_predicted_close = None
    lstm_metrics = None
    
    try:
        val_split = int(len(df_train) * 0.85)
        df_train_sub = df_train.iloc[:val_split]
        df_val = df_train.iloc[val_split - seq_length:]
        
        x_lstm_train, y_lstm_train, scaler_x_train, scaler_y_train = prepare_lstm_data(df_train_sub, seq_length)
        x_lstm_val, y_lstm_val, _, _ = prepare_lstm_data(df_val, seq_length, scaler_x_train, scaler_y_train)
        x_lstm_test, y_lstm_test, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x_train, scaler_y_train)
        
        cache_path_lstm = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_seq{seq_length}_model.keras")
        lstm_loaded = False
        lstm_status = "Trained LSTM model"
        
        if not force_retrain and os.path.exists(cache_path_lstm):
            meta_path_lstm = cache_path_lstm.replace(".keras", "_meta.json")
            is_cache_valid = False
            if os.path.exists(meta_path_lstm):
                try:
                    with open(meta_path_lstm, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    last_trained_str = meta_data.get("predicted_candle_start")
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    if last_trained_str and current_predicted_candle and current_predicted_candle <= last_trained_str:
                        is_cache_valid = True
                except Exception as e:
                    print(f"Error reading LSTM meta for {symbol}: {e}")
            if is_cache_valid:
                try:
                    model_lstm = tf.keras.models.load_model(cache_path_lstm)
                    lstm_loaded = True
                    lstm_status = f"Loaded cached LSTM model ({interval})"
                except Exception as e:
                    print(f"Error loading cached LSTM model for {symbol}: {e}")
        
        if not lstm_loaded:
            is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
            if is_auto_trained_asset and not force_retrain and not is_daemon:
                if os.path.exists(cache_path_lstm):
                    try:
                        model_lstm = tf.keras.models.load_model(cache_path_lstm)
                        lstm_loaded = True
                        lstm_status = f"Loaded cached LSTM model ({interval} - Fallback)"
                    except Exception as e:
                        print(f"Error loading fallback LSTM model for {symbol}: {e}")
                if not lstm_loaded:
                    raise ValueError(f"LSTM Model for {symbol} is currently training.")
            else:
                model_lstm = train_lstm_model(x_lstm_train, y_lstm_train, seq_length, validation_data=(x_lstm_val, y_lstm_val))
                model_lstm.save(cache_path_lstm)
                lstm_status = f"Trained LSTM model ({interval})"
                try:
                    meta_path_lstm = cache_path_lstm.replace(".keras", "_meta.json")
                    last_candle_start = df.index[-1]
                    current_predicted_candle = df.attrs.get("predicted_candle_start")
                    with open(meta_path_lstm, "w", encoding="utf-8") as f:
                        json.dump({
                            "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S"),
                            "predicted_candle_start": current_predicted_candle
                        }, f)
                except Exception:
                    pass
        
        lstm_metrics = evaluate_model_performance(model_lstm, x_lstm_test, y_lstm_test, scaler_y_train, df_test, seq_length)
        lstm_metrics["training_status"] = lstm_status
        
        last_features_lstm = df[FEATURES].iloc[-seq_length:].values
        scaled_last_features = scaler_x_train.transform(last_features_lstm)
        input_seq = np.array([scaled_last_features])
        prob_pred = model_lstm.predict(input_seq, verbose=0)
        lstm_predicted_close = float(prob_pred[0][0])
        
        # Free TensorFlow memory to prevent memory leaks during sequential model training
        try:
            import gc
            tf.keras.backend.clear_session()
            del model_lstm
            gc.collect()
        except Exception:
            pass

        
    except Exception as e:
        print(f"Error in LSTM flow: {e}")
        
    return lstm_predicted_close, lstm_metrics
