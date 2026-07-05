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

def delete_symbol_cache_files(symbol: str):
    """Deletes all cached model files for the specified symbol to keep cache clean."""
    if not os.path.exists(MODEL_CACHE_DIR):
        return
    deleted_count = 0
    prefix = f"{symbol}_"
    for filename in os.listdir(MODEL_CACHE_DIR):
        if filename.startswith(prefix):
            file_path = os.path.join(MODEL_CACHE_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
    if deleted_count > 0:
        print(f"Deleted {deleted_count} stale cache files for pending symbol {symbol}.")

def check_and_train_assets():
    """Runs daily model training sequentially for the popular cryptos, stocks, and commodities."""
    print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Starting Auto-Training loop...")
    
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
            res = get_prediction(symbol, interval="1d", force_retrain=False, is_daemon=True)
            
            # Check if prediction is pending due to data lag
            if res.get("prediction_status") == "pending_data":
                print(f"Skipped {symbol}: Daily candle is not yet complete. Deleting cache files.")
                delete_symbol_cache_files(symbol)
                fail_count += 1
                continue
                
            # Update screener table
            from backend.predictor import update_screener_cache
            db_run = SessionLocal()
            try:
                update_screener_cache(symbol, db_run)
            finally:
                db_run.close()
                
            success_count += 1
        except Exception as e:
            print(f"Error training {symbol}: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Auto-training cycle completed. Success: {success_count}, Failed/Pending: {fail_count}")
    cleanup_old_models()
    
    # Run daily mock trading choice and execution
    try:
        from backend.mock_trading import run_mock_trading_daily_buy
        run_mock_trading_daily_buy()
    except Exception as mock_err:
        print(f"Error executing daily mock buy: {mock_err}")

def cleanup_old_models():
    """Deletes any cached model files in model_cache that are older than 72 hours."""
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Cleaning up stale model files...")
    if not os.path.exists(MODEL_CACHE_DIR):
        return
        
    now = time.time()
    deleted_count = 0
    
    for filename in os.listdir(MODEL_CACHE_DIR):
        file_path = os.path.join(MODEL_CACHE_DIR, filename)
        if os.path.isfile(file_path) and (filename.endswith(".keras") or filename.endswith(".json") or filename.endswith(".pkl")):
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
    
    # Start background mock trading monitoring thread (runs every 5 minutes)
    try:
        import threading
        from backend.mock_trading import check_mock_trading_rule
        
        def run_mock_trading_monitor():
            print("[Mock Trading] Background monitor thread started.")
            # Sleep 15 seconds initially to let startup settle
            time.sleep(15)
            while True:
                try:
                    check_mock_trading_rule()
                except Exception as monitor_err:
                    print(f"[Mock Trading Monitor Error] {monitor_err}")
                time.sleep(300)
                
        monitor_thread = threading.Thread(target=run_mock_trading_monitor, daemon=True)
        monitor_thread.start()
    except Exception as thread_err:
        print(f"Error starting mock trading monitor thread: {thread_err}")
        
    # 1. Warm up cache immediately on startup
    check_and_train_assets()
    
    # 2. Main sleep-and-run loop
    while True:
        sleep_sec = get_seconds_until_next_run()
        next_run_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=sleep_sec)
        print(f"Daily training scheduled. Sleeping for {sleep_sec:.0f} seconds (approx {sleep_sec/3600:.2f} hours) until next scheduled run at {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} UTC...")
        time.sleep(sleep_sec)
        
        # Trigger daily training once
        check_and_train_assets()

if __name__ == "__main__":
    main()
