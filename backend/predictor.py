import os
import json
import requests
import datetime
import pickle
import pandas as pd
import numpy as np
import tensorflow as tf
import xgboost as xgb
from typing import Dict, List, Any, Optional

# Import constants and sub-module functions for re-exporting (Facade pattern)
from backend.config import MODEL_CACHE_DIR, DEFAULT_SEQUENCE_LENGTH, AUTO_TRAINED_SYMBOLS, TICKER_NAMES, FEATURES
from backend.indicators import calculate_rsi, calculate_macd, calculate_atr
from backend.data_fetcher import fetch_binance_data, fetch_market_data, fetch_interval_history
from backend.sentiment import analyze_text_sentiment, fetch_symbol_news, get_fundamental_analysis
from backend.prediction_engine import (
    prepare_lstm_data, train_lstm_model, 
    evaluate_model_performance, evaluate_xgb_performance,
    train_lr_model, evaluate_lr_performance
)

def get_prediction(
    symbol: str, 
    interval: str = "1d", 
    seq_length: int = DEFAULT_SEQUENCE_LENGTH, 
    lang: str = "en", 
    force_retrain: bool = False, 
    model_type: str = "xgboost", 
    is_daemon: bool = False
) -> Dict[str, Any]:
    """
    Main function to coordinate market data retrieval, model loading/training,
    and predicting the next close price for a specific interval (15m, 1h, 4h, 1d).
    Supports 'xgboost' (default) and 'lstm' architectures.
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

        if model_type == "xgboost":
            # --- XGBoost Model Flow ---
            # Validation split for early stopping
            val_split = int(len(df_train) * 0.85)
            df_train_sub = df_train.iloc[:val_split]
            df_val = df_train.iloc[val_split - seq_length:]
            
            def make_raw_xgb_sequences(x_data, y_data):
                xs, ys = [], []
                for i in range(seq_length, len(x_data)):
                    xs.append(x_data[i-seq_length:i])
                    ys.append(y_data[i])
                return np.array(xs).reshape(len(xs), -1), np.array(ys)
                
            x_xgb_train, y_xgb_train = make_raw_xgb_sequences(df_train_sub[FEATURES].values, df_train_sub["Daily_Return"].values)
            x_xgb_val, y_xgb_val = make_raw_xgb_sequences(df_val[FEATURES].values, df_val["Daily_Return"].values)
            x_xgb_test, y_xgb_test = make_raw_xgb_sequences(df_test[FEATURES].values, df_test["Daily_Return"].values)
            
            cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model.json")
            model_loaded = False
            
            # Check if cached model exists and is up to date
            if not force_retrain and os.path.exists(cache_path):
                meta_path = cache_path.replace(".json", "_meta.json")
                is_cache_valid = False
                
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta_data = json.load(f)
                        last_trained_str = meta_data.get("last_candle_start")
                        if last_trained_str:
                            last_trained_candle_start = datetime.datetime.strptime(last_trained_str, "%Y-%m-%d %H:%M:%S")
                            last_candle_start = df.index[-1]
                            if last_candle_start <= last_trained_candle_start:
                                is_cache_valid = True
                    except Exception as meta_err:
                        print(f"Error reading model metadata: {meta_err}")
                        
                if is_cache_valid:
                    try:
                        model = xgb.XGBRegressor()
                        model.load_model(cache_path)
                        model_loaded = True
                        training_status = f"Loaded cached XGBoost model ({interval} - fully up-to-date)"
                    except Exception:
                        pass
                        
            if not model_loaded:
                is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")
                
                if is_auto_trained_asset and not force_retrain and not is_daemon:
                    if os.path.exists(cache_path):
                        try:
                            model = xgb.XGBRegressor()
                            model.load_model(cache_path)
                            model_loaded = True
                            training_status = f"Loaded cached XGBoost model ({interval} - Stale/Fallback)"
                        except Exception:
                            pass
                    if not model_loaded:
                        raise ValueError(f"XGBoost Model for {symbol} is currently being initialized/trained on the server. Please try again in a few minutes.")
                else:
                    model = xgb.XGBRegressor(
                        n_estimators=500,
                        max_depth=6,
                        learning_rate=0.03,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        reg_alpha=0.1,
                        reg_lambda=1,
                        early_stopping_rounds=15,
                        random_state=42,
                        n_jobs=-1
                    )
                    model.fit(
                        x_xgb_train, y_xgb_train,
                        eval_set=[(x_xgb_val, y_xgb_val)],
                        verbose=False
                    )
                    metrics = evaluate_xgb_performance(model, x_xgb_test, df_test, seq_length)
                    model.save_model(cache_path)
                    training_status = f"Trained XGBoost model on 80% train data ({interval} timeframe)"
                    
                    try:
                        meta_path = cache_path.replace(".json", "_meta.json")
                        last_candle_start = df.index[-1]
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S")
                            }, f)
                    except Exception as meta_err:
                        print(f"Error saving model metadata for {symbol}: {meta_err}")
                        
            if model_loaded:
                metrics = evaluate_xgb_performance(model, x_xgb_test, df_test, seq_length)
                
            metrics["training_status"] = training_status
            
            # Predict the next close price using the last seq_length candles
            last_features = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
            predicted_return = float(model.predict(last_features)[0])
            
        elif model_type == "linear_regression":
            if symbol != "BTC-USD":
                raise ValueError("Linear Regression is currently only available for Bitcoin (BTC-USD).")
                
            def make_raw_lr_sequences(x_data, y_data):
                xs, ys = [], []
                for i in range(seq_length, len(x_data)):
                    xs.append(x_data[i-seq_length:i])
                    ys.append(y_data[i])
                return np.array(xs).reshape(len(xs), -1), np.array(ys)
                
            x_lr_train, y_lr_train = make_raw_lr_sequences(df_train[FEATURES].values, df_train["Daily_Return"].values)
            x_lr_test, y_lr_test = make_raw_lr_sequences(df_test[FEATURES].values, df_test["Daily_Return"].values)
            
            cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model_lr.pkl")
            model_loaded = False
            
            # Check if cached model exists and is up to date
            if not force_retrain and os.path.exists(cache_path):
                meta_path = cache_path.replace("_lr.pkl", "_lr_meta.json")
                is_cache_valid = False
                
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta_data = json.load(f)
                        last_trained_str = meta_data.get("last_candle_start")
                        if last_trained_str:
                            last_trained_candle_start = datetime.datetime.strptime(last_trained_str, "%Y-%m-%d %H:%M:%S")
                            last_candle_start = df.index[-1]
                            if last_candle_start <= last_trained_candle_start:
                                is_cache_valid = True
                    except Exception as meta_err:
                        print(f"Error reading linear regression model metadata: {meta_err}")
                        
                if is_cache_valid:
                    try:
                        with open(cache_path, "rb") as f:
                            model = pickle.load(f)
                        model_loaded = True
                        training_status = f"Loaded cached Linear Regression model ({interval} - fully up-to-date)"
                    except Exception:
                        pass
                        
            if not model_loaded:
                model = train_lr_model(x_lr_train, y_lr_train)
                metrics = evaluate_lr_performance(model, x_lr_test, df_test, seq_length)
                
                with open(cache_path, "wb") as f:
                    pickle.dump(model, f)
                training_status = f"Trained Linear Regression model on 80% train data ({interval} timeframe)"
                
                try:
                    meta_path = cache_path.replace("_lr.pkl", "_lr_meta.json")
                    last_candle_start = df.index[-1]
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "last_candle_start": last_candle_start.strftime("%Y-%m-%d %H:%M:%S")
                        }, f)
                except Exception as meta_err:
                    print(f"Error saving linear regression model metadata for {symbol}: {meta_err}")
                    
            if model_loaded:
                metrics = evaluate_lr_performance(model, x_lr_test, df_test, seq_length)
                
            metrics["training_status"] = training_status
            
            # Predict the next close price using the last seq_length candles
            last_features = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
            predicted_return = float(model.predict(last_features)[0])
            
        else:
            # --- LSTM Model Flow ---
            # Split train data into sub-train (85%) and validation (15%) for chronological early stopping
            val_split = int(len(df_train) * 0.85)
            df_train_sub = df_train.iloc[:val_split]
            df_val = df_train.iloc[val_split - seq_length:]

            # Fit scalers ONLY on train_sub data — validation & test data must never influence the scalers
            x_lstm_train, y_lstm_train, scaler_x_train, scaler_y_train = prepare_lstm_data(df_train_sub, seq_length)
            
            # Scale validation and test data using the train_sub scalers (no data leakage!)
            x_lstm_val, y_lstm_val, _, _ = prepare_lstm_data(df_val, seq_length, scaler_x_train, scaler_y_train)
            x_lstm_test, y_lstm_test, _, _ = prepare_lstm_data(df_test, seq_length, scaler_x_train, scaler_y_train)

            # Check if cached model exists for this specific interval
            cache_path = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model.keras")
            model_loaded = False

            # Check if cached model exists and is up to date relative to the latest completed candle start
            if not force_retrain and os.path.exists(cache_path):
                meta_path = cache_path.replace(".keras", "_meta.json")
                is_cache_valid = False

                if os.path.exists(meta_path):
                    try:
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
                        training_status = f"Loaded cached LSTM model ({interval} - fully up-to-date)"
                    except Exception:
                        pass  # If load fails, we will re-train

            if not model_loaded:
                is_auto_trained_asset = (symbol in AUTO_TRAINED_SYMBOLS) and (interval == "1d")

                if is_auto_trained_asset and not force_retrain and not is_daemon:
                    # Standard user request: do NOT train on the fly. Try loading stale/older cached model
                    if os.path.exists(cache_path):
                        try:
                            model = tf.keras.models.load_model(cache_path)
                            model_loaded = True
                            training_status = f"Loaded cached LSTM model ({interval} - Stale/Fallback)"
                        except Exception:
                            pass

                    # If still not loaded (e.g. no cache file exists yet), raise error
                    if not model_loaded:
                        raise ValueError(f"LSTM Model for {symbol} is currently being initialized/trained on the server. Please try again in a few minutes.")
                else:
                    # Train model ONLY on the train_sub split with explicit validation_data (no data leakage)
                    model = train_lstm_model(x_lstm_train, y_lstm_train, seq_length, validation_data=(x_lstm_val, y_lstm_val))

                    # Evaluate on the held-out 20% test data (out-of-sample, read-only — no fine-tuning)
                    metrics = evaluate_model_performance(model, x_lstm_test, y_lstm_test, scaler_y_train, df_test, seq_length)

                    # Save the model trained purely on train data
                    model.save(cache_path)
                    training_status = f"Trained LSTM model on 80% train data ({interval} timeframe)"

                    # Save model metadata containing the start time of the last completed candle
                    try:
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
                # Evaluate using train_sub scalers (consistent with how the model was originally trained)
                metrics = evaluate_model_performance(model, x_lstm_test, y_lstm_test, scaler_y_train, df_test, seq_length)

            # Predict the next close price using the last seq_length candles
            last_features = df[FEATURES].iloc[-seq_length:].values
            scaled_last_features = scaler_x_train.transform(last_features)
            input_seq = np.array([scaled_last_features])
            scaled_pred = model.predict(input_seq, verbose=0)
            predicted_return = float(scaler_y_train.inverse_transform(scaled_pred)[0][0])

        metrics["training_status"] = training_status

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
        "prediction_error": pending_error_msg,
        "model_type": model_type
    }

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
        
        # 2. Get the latest daily market data for technical indicators
        df, name, _, _ = fetch_market_data(symbol_upper, interval="1d")
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
