import os
import sys
import time
import datetime
import traceback

# Ensure parent directory is in python path if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predictor import get_prediction
from backend.config import MODEL_CACHE_DIR, AUTO_TRAINED_SYMBOLS
from backend.database import SessionLocal
from backend.models import AutoTrainSymbol

def check_and_train_assets():
    """Runs daily model training sequentially for the popular cryptos, stocks, and commodities."""
    print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Starting Daily Auto-Training loop...")
    
    # Query database for symbols, fall back to config if empty or error
    db = SessionLocal()
    try:
        db_symbols = [s.symbol for s in db.query(AutoTrainSymbol).order_by(AutoTrainSymbol.symbol).all()]
        symbols = db_symbols if db_symbols else AUTO_TRAINED_SYMBOLS
    except Exception as e:
        print(f"Error loading auto-train symbols from DB: {e}")
        symbols = AUTO_TRAINED_SYMBOLS
    finally:
        db.close()

    success_count = 0
    fail_count = 0
    
    for idx, symbol in enumerate(symbols):
        try:
            print(f"[{idx+1}/{len(symbols)}] Training/Updating cache for {symbol} (1d)...")
            get_prediction(symbol, interval="1d", force_retrain=True)
            success_count += 1
        except Exception as e:
            print(f"Error training {symbol}: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Auto-training cycle completed. Success: {success_count}, Failed: {fail_count}")
    cleanup_old_models()

def cleanup_old_models():
    """Deletes any cached model files in model_cache that are older than 72 hours."""
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Cleaning up stale model files...")
    if not os.path.exists(MODEL_CACHE_DIR):
        return
        
    now = time.time()
    deleted_count = 0
    
    for filename in os.listdir(MODEL_CACHE_DIR):
        file_path = os.path.join(MODEL_CACHE_DIR, filename)
        if os.path.isfile(file_path) and filename.endswith(".keras"):
            mtime = os.path.getmtime(file_path)
            age_hours = (now - mtime) / 3600
            # Delete if model has not been updated in the last 72 hours (prevents weekend stock model deletion)
            if age_hours > 72:
                try:
                    os.remove(file_path)
                    print(f"Deleted stale model: {filename} (age: {age_hours:.1f} hours)")
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
                    
    print(f"Cleanup finished. Stale models deleted: {deleted_count}")

def get_seconds_until_next_run():
    """Calculates seconds remaining until the next run at 00:05 UTC."""
    now = datetime.datetime.utcnow()
    target = now.replace(hour=0, minute=5, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(days=1)
    diff = (target - now).total_seconds()
    return diff

def main():
    print("====================================================")
    print("Daily Asset Auto-Training Daemon Started!")
    print("====================================================")
    
    # 1. Warm up cache immediately on startup (for missing or stale models)
    check_and_train_assets()
    
    # 2. Main sleep-and-run loop
    while True:
        sleep_sec = get_seconds_until_next_run()
        next_run_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=sleep_sec)
        print(f"Sleeping for {sleep_sec:.0f} seconds (approx {sleep_sec/3600:.2f} hours) until next scheduled run at {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} UTC...")
        time.sleep(sleep_sec)
        
        # Trigger training
        check_and_train_assets()

if __name__ == "__main__":
    main()
