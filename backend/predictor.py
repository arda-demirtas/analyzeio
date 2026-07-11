import os
import json
import requests
import datetime
import pickle
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

# Import constants and sub-module functions for re-exporting (Facade pattern)
from backend.config import MODEL_CACHE_DIR, DEFAULT_SEQUENCE_LENGTH, AUTO_TRAINED_SYMBOLS, TICKER_NAMES, FEATURES
from backend.indicators import calculate_rsi, calculate_macd, calculate_atr
from backend.data_fetcher import fetch_binance_data, fetch_market_data, fetch_interval_history
from backend.sentiment import analyze_text_sentiment, fetch_symbol_news, get_fundamental_analysis

from backend.model_xgb_handler import get_xgb_prediction
from backend.model_lstm_handler import get_lstm_prediction
from backend.model_lr_handler import get_lr_prediction
from backend.model_patchtst_handler import get_patchtst_prediction
from backend.model_sr_handler import get_sr_prediction
from backend.prediction_engine import train_lr_model


def get_prediction(
    symbol: str, 
    interval: str = "1d", 
    seq_length: int = DEFAULT_SEQUENCE_LENGTH, 
    lang: str = "en", 
    force_retrain: bool = False, 
    model_type: str = "analyzeio",
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

    # We no longer support pending_data states. The models will run using the latest available data.
    is_pending_data = False
    pending_error_msg = None

    predicted_close = None
    change_percent = None
    metrics = None
    xgb_predicted_close = None
    lstm_predicted_close = None
    lr_predicted_close = None
    patchtst_predicted_close = None
    sr_predicted_close = None

    xgb_metrics = None
    lstm_metrics = None
    lr_metrics = None
    patchtst_metrics = None
    sr_metrics = None

    if not is_pending_data:
        split_idx = int(len(df) * 0.8)
        df_train = df.iloc[:split_idx]
        df_test = df.iloc[split_idx - seq_length:]

        # Max/min return bounds
        max_ret = 0.15 if is_crypto else 0.08
        min_ret = -0.15 if is_crypto else -0.08

        # A. XGBoost Flow
        try:
            xgb_predicted_close, xgb_metrics = get_xgb_prediction(
                symbol, interval, df, df_train, df_test, seq_length, force_retrain, is_daemon, max_ret, min_ret
            )
        except Exception as e:
            print(f"Error in XGBoost flow: {e}")
            xgb_predicted_close, xgb_metrics = None, None

        # B. LSTM Flow
        try:
            lstm_predicted_close, lstm_metrics = get_lstm_prediction(
                symbol, interval, df, df_train, df_test, seq_length, force_retrain, is_daemon, max_ret, min_ret
            )
        except Exception as e:
            print(f"Error in LSTM flow: {e}")
            lstm_predicted_close, lstm_metrics = None, None

        # C. Linear Regression Flow
        try:
            lr_predicted_close, lr_metrics = get_lr_prediction(
                symbol, interval, df, df_train, df_test, seq_length, force_retrain, is_daemon, max_ret, min_ret
            )
        except Exception as e:
            print(f"Error in Linear Regression flow: {e}")
            lr_predicted_close, lr_metrics = None, None

        # D. PatchTST Flow
        try:
            patchtst_predicted_close, patchtst_metrics = get_patchtst_prediction(
                symbol, interval, df, df_train, df_test, seq_length, force_retrain, is_daemon, max_ret, min_ret
            )
        except Exception as e:
            print(f"Error in PatchTST flow: {e}")
            patchtst_predicted_close, patchtst_metrics = None, None

        # E. Support/Resistance Flow
        try:
            sr_predicted_close, sr_metrics = get_sr_prediction(
                symbol, interval, df, df_train, df_test, seq_length, force_retrain, is_daemon, max_ret, min_ret
            )
        except Exception as e:
            print(f"Error in S/R flow: {e}")
            sr_predicted_close, sr_metrics = None, None

    # Details of the last available candle
    last_row = df.iloc[-1]
    last_close = float(last_row["Close"])

    is_pending_prediction = (xgb_predicted_close is None or 
                             lstm_predicted_close is None or 
                             lr_predicted_close is None or 
                             patchtst_predicted_close is None or
                             sr_predicted_close is None)

    if not is_pending_data and not is_pending_prediction:
        # "analyzeio" is the average of all 5 models!
        analyzeio_predicted_close = (xgb_predicted_close + lstm_predicted_close + lr_predicted_close + patchtst_predicted_close + sr_predicted_close) / 5.0
            
        # Average performance metrics
        valid_metrics_list = [xgb_metrics, lstm_metrics, lr_metrics, patchtst_metrics, sr_metrics]
        avg_logloss = sum(m.get("logloss", 0.693) for m in valid_metrics_list) / 5.0
        avg_da = sum(m.get("directional_accuracy", 50.0) for m in valid_metrics_list) / 5.0
        analyzeio_metrics = {
            "logloss": avg_logloss,
            "directional_accuracy": avg_da,
            "training_status": "Average of 5 models (Analyzeio)"
        }

        if model_type == "lstm":
            predicted_close = lstm_predicted_close
            metrics = lstm_metrics
        elif model_type == "support_resistance":
            predicted_close = sr_predicted_close
            metrics = sr_metrics
        elif model_type == "linear_regression":
            predicted_close = lr_predicted_close
            metrics = lr_metrics
        elif model_type == "patchtst":
            predicted_close = patchtst_predicted_close
            metrics = patchtst_metrics
        elif model_type == "xgboost":
            predicted_close = xgb_predicted_close
            metrics = xgb_metrics
        else:
            predicted_close = analyzeio_predicted_close
            metrics = analyzeio_metrics
    else:
        # If any model is missing/training, the ensemble and all outputs are pending (None)
        analyzeio_predicted_close = None
        analyzeio_metrics = None
        predicted_close = None
        metrics = None


    candle_open_time = None
    candle_close_time = None

    # Calculate expected close time of the predicted candle using UTC explicitly
    if interval == "1d":
        last_date_str = last_row.name.strftime("%Y-%m-%d")
        now_utc = datetime.datetime.utcnow()
        if is_crypto:
            # Daily crypto candle closes at 00:00 UTC
            pred_date = now_utc.date()
            close_time = datetime.datetime.combine(pred_date, datetime.time.min) + datetime.timedelta(days=1)
            expected_close_time = f"{close_time.strftime('%Y-%m-%d')} 03:00 (TRT)"
            candle_open_time = f"{pred_date.strftime('%Y-%m-%d')} 03:00 (TRT)"
            candle_close_time = expected_close_time
        else:
            # Determine close hour in UTC
            if symbol.endswith(".IS"):
                close_hour_utc = 15  # BIST closes at 18:00 TRT (15:00 UTC)
                close_time_str = "18:00 (TRT)"
                open_time_str = "10:00 (TRT)"
            else:
                close_hour_utc = 20  # US markets close at 16:00 EST (20:00 UTC)
                close_time_str = "23:00 (TRT)"
                open_time_str = "16:30 (TRT)"

            # If current UTC hour is past market close, target is the next day
            if now_utc.hour >= close_hour_utc:
                pred_date = now_utc.date() + datetime.timedelta(days=1)
            else:
                pred_date = now_utc.date()

            # Skip weekends (Saturday=5, Sunday=6)
            while pred_date.weekday() in [5, 6]:
                pred_date += datetime.timedelta(days=1)

            expected_close_time = f"{pred_date.strftime('%Y-%m-%d')} {close_time_str}"
            candle_open_time = f"{pred_date.strftime('%Y-%m-%d')} {open_time_str}"
            candle_close_time = expected_close_time

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
        candle_open_time = f"{last_row.name.strftime('%Y-%m-%d %H:%M')} (TRT)"
        candle_close_time = expected_close_time
        
    if not is_pending_data and not is_pending_prediction:
        valid_predictions = [
            v for v in [xgb_predicted_close, lstm_predicted_close, lr_predicted_close, patchtst_predicted_close]
            if v is not None
        ]
        if valid_predictions:
            avg_predicted_prob = sum(valid_predictions) / len(valid_predictions)
            change_percent = (avg_predicted_prob - 0.5) * 100
        else:
            change_percent = 0.0
    else:
        change_percent = None
    
    # Calculate threshold-filtered technical recommendation (4% confidence threshold, equivalent to 54% probability limit)
    if is_pending_data or is_pending_prediction:
        tech_signal = "HOLD"
        if lang == "tr":
            tech_text = "Modellerin eğitimi veya veri güncellemesi sürüyor. Lütfen bekleyin..."
        elif lang == "de":
            tech_text = "Modelltraining oder Datenaktualisierung läuft. Bitte warten..."
        elif lang == "ru":
            tech_text = "Обучение моделей или обновление данных продолжается. Пожалуйста, подождите..."
        elif lang == "zh":
            tech_text = "模型训练或数据更新中。请稍候..."
        elif lang == "es":
            tech_text = "El entrenamiento del modelo o la actualización de datos está en curso. Por favor, espere..."
        else:
            tech_text = "Model training or data update is in progress. Please wait..."
    elif change_percent > 4.0:
        tech_signal = "STRONG_BUY"
        if lang == "tr":
            tech_text = "Modellerin ortalama tahmini, yüksek güvenilirlikli yukarı yönlü ivme öngörüyor (>54%). Long (Alış) pozisyonu açılması önerilir."
        elif lang == "de":
            tech_text = "Die durchschnittliche Prognose der Modelle deutet auf eine hohe Aufwärtsdynamik (>54%) hin. Die Eröffnung einer Long-Position wird empfohlen."
        elif lang == "ru":
            tech_text = "Средний прогноз моделей указывает на восходящий импульс высокой степени надежности (>54%). Рекомендуется открыть позицию Long."
        elif lang == "zh":
            tech_text = "模型的平均预测显示高置信度上行趋势 (>54%)。建议开立多单（做多）。"
        elif lang == "es":
            tech_text = "El pronóstico promedio de los modelos indica un impulso alcista de alta convicción (>54%). Se recomienda abrir una posición Long."
        else:
            tech_text = "Models' average prediction forecasts high-conviction upward momentum (>54%). Opening a Long position is recommended."
    elif change_percent < -4.0:
        tech_signal = "STRONG_SELL"
        if lang == "tr":
            tech_text = "Modellerin ortalama tahmini, yüksek güvenilirlikli aşağı yönlü ivme öngörüyor (<46%). Short (Satış) pozisyonu açılması veya Nakitte kalınması önerilir."
        elif lang == "de":
            tech_text = "Die durchschnittliche Prognose der Modelle deutet auf eine hohe Abwärtsdynamik (<46%) hin. Die Eröffnung einer Short-Position oder das Verbleiben in bar wird empfohlen."
        elif lang == "ru":
            tech_text = "Средний прогноз моделей указывает на нисходящий импульс высокой степени надежности (<46%). Рекомендуется открыть позицию Short или оставаться в кэше."
        elif lang == "zh":
            tech_text = "模型的平均预测显示高置信度下行趋势 (<46%)。建议开立空单（做空）或持有现金。"
        elif lang == "es":
            tech_text = "El pronóstico promedio de los modelos indica un impulso bajista de alta convicción (<46%). Se recomienda abrir una posición Short o permanecer en Efectivo."
        else:
            tech_text = "Models' average prediction forecasts high-conviction downward momentum (<46%). Opening a Short position or staying in Cash is recommended."
    else:
        tech_signal = "HOLD"
        if lang == "tr":
            tech_text = "Modellerin ortalama tahmini, kararsız yön öngörüyor (46% ile 54% arasında). Nakitte kalınması önerilir."
        elif lang == "de":
            tech_text = "Die durchschnittliche Prognose der Modelle deutet auf eine unklare Richtung hin (zwischen 46% und 54%). Es wird empfohlen, in bar zu bleiben."
        elif lang == "ru":
            tech_text = "Средний прогноз моделей указывает на неопределенное направление цены (между 46% ve 54%). Rekomenduetsya ostavatsya v keshe."
        elif lang == "zh":
            tech_text = "模型的平均预测显示方向不明（在 46% 至 54% 之间）。建议持有现金。"
        elif lang == "es":
            tech_text = "El pronóstico promedio de los modelos indica una dirección incierta (entre 46% y 54%). Se recomienda permanecer en Efectivo."
        else:
            tech_text = "Models' average prediction forecasts uncertain direction (between 46% and 54%). Staying in Cash is recommended."
            
    technical_recommendation = {
        "signal": tech_signal,
        "text": tech_text
    }
    
    # Load model_lr from cache for historical chart predictions
    model_lr = None
    cache_path_lr = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model_lr.pkl")
    if os.path.exists(cache_path_lr):
        try:
            with open(cache_path_lr, "rb") as f:
                model_lr = pickle.load(f)
        except Exception:
            pass
            
    chart_limit = 730
    history_df = df.tail(chart_limit)
    df_indices = {dt: idx for idx, dt in enumerate(df.index)}
    
    history_list = []
    for idx, row in history_df.iterrows():
        if interval == "1d":
            date_str = idx.strftime("%Y-%m-%d")
        else:
            date_str = idx.strftime("%Y-%m-%d %H:%M")
            
        lr_hist_val = None
        if model_lr is not None:
            pos = df_indices.get(idx)
            if pos is not None and pos >= seq_length:
                try:
                    feat_seq = df[FEATURES].iloc[pos - seq_length : pos].values.flatten().reshape(1, -1)
                    pred_prob = float(model_lr.predict_proba(feat_seq)[0][1])
                    prev_close = float(df["Close"].iloc[pos - 1])
                    lr_hist_val = float(prev_close * (1 + (pred_prob - 0.5) * 0.04))
                except Exception:
                    pass
            
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
            "lr_predicted_close": lr_hist_val
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
        if not is_pending_data and not is_pending_prediction:
            existing_log = (
                db_session.query(PredictionLog)
                .filter(
                    PredictionLog.symbol == symbol,
                    PredictionLog.interval == interval,
                    PredictionLog.prediction_date == pred_date_str
                )
                .first()
            )
            
            # Find the best model's prediction probability to log
            models_da = []
            if xgb_predicted_close is not None and xgb_metrics and xgb_metrics.get("directional_accuracy") is not None:
                models_da.append((xgb_metrics["directional_accuracy"], xgb_predicted_close))
            if lstm_predicted_close is not None and lstm_metrics and lstm_metrics.get("directional_accuracy") is not None:
                models_da.append((lstm_metrics["directional_accuracy"], lstm_predicted_close))
            if lr_predicted_close is not None and lr_metrics and lr_metrics.get("directional_accuracy") is not None:
                models_da.append((lr_metrics["directional_accuracy"], lr_predicted_close))
            if patchtst_predicted_close is not None and patchtst_metrics and patchtst_metrics.get("directional_accuracy") is not None:
                models_da.append((patchtst_metrics["directional_accuracy"], patchtst_predicted_close))

            best_model_predicted_close = predicted_close # fallback to ensemble
            if models_da:
                models_da.sort(key=lambda x: x[0], reverse=True)
                best_model_predicted_close = models_da[0][1]

            if best_model_predicted_close is not None:
                if existing_log:
                    existing_log.predicted_close = best_model_predicted_close
                    existing_log.last_close = last_close
                    existing_log.created_at = datetime.datetime.utcnow()
                else:
                    new_log = PredictionLog(
                        symbol=symbol,
                        interval=interval,
                        prediction_date=pred_date_str,
                        predicted_close=best_model_predicted_close,
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
        "candle_open_time": candle_open_time,
        "candle_close_time": candle_close_time,
        "price_change_percent": change_percent,
        "current_price": current_price,
        "metrics": metrics,
        "history": history_list,
        "fundamental_analysis": fundamental_result,
        "technical_recommendation": technical_recommendation,
        "prediction_status": "pending" if (is_pending_data or is_pending_prediction) else "success",
        "prediction_error": "Modellerin eğitimi sürüyor. Lütfen bekleyin..." if is_pending_prediction else pending_error_msg,
        "model_type": model_type,
        "has_today_candle": df.attrs.get("has_today_candle", False),
        "xgb_predicted_close": xgb_predicted_close,
        "lstm_predicted_close": lstm_predicted_close,
        "lr_predicted_close": lr_predicted_close,
        "patchtst_predicted_close": patchtst_predicted_close,
        "sr_predicted_close": sr_predicted_close,
        "analyzeio_predicted_close": analyzeio_predicted_close,
        "xgb_metrics": xgb_metrics,
        "lstm_metrics": lstm_metrics,
        "lr_metrics": lr_metrics,
        "patchtst_metrics": patchtst_metrics,
        "sr_metrics": sr_metrics,
        "analyzeio_metrics": analyzeio_metrics
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
