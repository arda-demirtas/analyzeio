import os
import sys
import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend.models import MarketScreener, PredictionLog
from backend.predictor import fetch_market_data, TICKER_NAMES
from backend.config import AUTO_TRAINED_SYMBOLS

def main():
    db = SessionLocal()
    try:
        print(f"Starting warmup for {len(AUTO_TRAINED_SYMBOLS)} symbols...")
        for idx, sym in enumerate(AUTO_TRAINED_SYMBOLS):
            try:
                print(f"[{idx+1}/{len(AUTO_TRAINED_SYMBOLS)}] Warming up {sym}...")
                df, asset_name, is_crypto, current_price = fetch_market_data(sym, interval="1d")
                if df.empty:
                    print(f"Empty data for {sym}")
                    continue
                    
                last_row = df.iloc[-1]
                price = current_price if current_price is not None else float(last_row["Close"])
                rsi = float(last_row["RSI"]) if "RSI" in last_row and not pd.isna(last_row["RSI"]) else 50.0
                macd_hist = float(last_row["MACD_Hist"]) if "MACD_Hist" in last_row and not pd.isna(last_row["MACD_Hist"]) else 0.0
                macd_signal = "BULLISH" if macd_hist > 0 else "BEARISH" if macd_hist < 0 else "NEUTRAL"
                
                log = (
                    db.query(PredictionLog)
                    .filter(PredictionLog.symbol == sym, PredictionLog.interval == "1d")
                    .order_by(PredictionLog.prediction_date.desc())
                    .first()
                )
                
                predicted_change = 0.0
                if log:
                    predicted_change = ((log.predicted_close - log.last_close) / log.last_close) * 100
                    # Clip changes to prevent outliers
                    max_c = 15.0 if is_crypto else 8.0
                    min_c = -15.0 if is_crypto else -8.0
                    if predicted_change > max_c:
                        predicted_change = max_c
                    elif predicted_change < min_c:
                        predicted_change = min_c
                    
                name = TICKER_NAMES.get(sym, sym)
                
                screener_entry = db.query(MarketScreener).filter(MarketScreener.symbol == sym).first()
                if screener_entry:
                    screener_entry.price = price
                    screener_entry.predicted_change = predicted_change
                    screener_entry.rsi = rsi
                    screener_entry.macd_signal = macd_signal
                    screener_entry.name = name
                    screener_entry.updated_at = datetime.datetime.utcnow()
                else:
                    new_entry = MarketScreener(
                        symbol=sym,
                        name=name,
                        price=price,
                        predicted_change=predicted_change,
                        rsi=rsi,
                        macd_signal=macd_signal
                    )
                    db.add(new_entry)
                db.commit()
            except Exception as e:
                print(f"Error warming up {sym}: {e}")
                db.rollback()
        print("Warmup finished successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
