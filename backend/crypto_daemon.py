import os
import sys
import time
import datetime
import traceback
import json

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
    """Checks all symbols to see if their cache is outdated compared to the latest completed candle.
    If outdated, deletes cache immediately (triggering pending on UI) and retrains from scratch.
    """
    print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Starting Hourly Cache Verification and Auto-Training Loop...")
    
    db = SessionLocal()
    try:
        db_symbols = [s.symbol for s in db.query(AutoTrainSymbol).order_by(AutoTrainSymbol.symbol).all()]
        symbols = db_symbols if db_symbols else AUTO_TRAINED_SYMBOLS
    except Exception as e:
        print(f"Error loading auto-train symbols from DB: {e}")
        symbols = AUTO_TRAINED_SYMBOLS
    finally:
        db.close()

    from backend.data_fetcher import fetch_market_data

    success_count = 0
    skipped_count = 0
    fail_count = 0
    
    for idx, symbol in enumerate(symbols):
        try:
            print(f"\n[{idx+1}/{len(symbols)}] Checking status for {symbol} (1d)...")
            
            # 1. Fetch live market data to find the latest completed candle
            try:
                df, _, _, _ = fetch_market_data(symbol, interval="1d")
                if df.empty:
                    raise ValueError("Dataframe is empty")
                current_candle_start = df.attrs.get("predicted_candle_start")
            except Exception as fe:
                print(f"  -> Error fetching market data for {symbol}: {fe}. Skipping for now.")
                fail_count += 1
                continue

            # 2. Check if cached metadata is up-to-date
            meta_path_xgb = os.path.join(MODEL_CACHE_DIR, f"{symbol}_1d_model_meta.json")
            cache_valid = False
            cached_candle = None
            if os.path.exists(meta_path_xgb):
                try:
                    with open(meta_path_xgb, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                    cached_candle = meta_data.get("predicted_candle_start")
                    if cached_candle and current_candle_start and cached_candle >= current_candle_start:
                        cache_valid = True
                except Exception:
                    pass

            # 3. Decision
            if cache_valid:
                print(f"  -> Cache is up-to-date (Current Candle: {current_candle_start}). Loading from cache to sync database...")
                try:
                    get_prediction(symbol, interval="1d", force_retrain=False, is_daemon=True)
                except Exception as sync_err:
                    print(f"     Failed to load prediction from cache to sync DB: {sync_err}")
                skipped_count += 1
                continue
            
            # Cache is outdated or missing! Delete and retrain.
            print(f"  -> Cache is OUTDATED or MISSING (Market: {current_candle_start}, Cache: {cached_candle}).")
            print(f"  -> Deleting old prediction files to show pending state on UI...")
            delete_symbol_cache_files(symbol)
            
            print(f"  -> Starting training from scratch for {symbol}...")
            res = get_prediction(symbol, interval="1d", force_retrain=True, is_daemon=True)
            
            # Update screener table
            from backend.predictor import update_screener_cache
            db_run = SessionLocal()
            try:
                update_screener_cache(symbol, db_run)
            finally:
                db_run.close()
                
            print(f"  -> Training successful for {symbol} (Candle: {current_candle_start})")
            success_count += 1
        except Exception as e:
            print(f"  -> Error training {symbol}: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Auto-training cycle completed.")
    print(f"Summary -> Success: {success_count}, Skipped (Up-to-date): {skipped_count}, Failed: {fail_count}")
    
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

def get_seconds_until_next_hourly_retry() -> float:
    """Calculates seconds remaining until the next hour's 05-minute mark (e.g., 01:05, 02:05, etc.)."""
    now = datetime.datetime.utcnow()
    target = now.replace(minute=5, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(hours=1)
    return (target - now).total_seconds()

def main():
    print("====================================================")
    print("Asset Auto-Training Daemon Started (Hourly Active Mode)!")
    print("====================================================")
    
    # Start background mock trading monitoring thread (runs every 5 minutes)
    try:
        import threading
        from backend.mock_trading import check_mock_trading_rule
        
        def run_mock_trading_monitor():
            print("[Mock Trading] Background monitor thread started.")
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
        
    # 1. Check and train immediately on startup
    check_and_train_assets()
    
    # 2. Main hourly active check loop
    while True:
        sec_to_retry = get_seconds_until_next_hourly_retry()
        print(f"Sleeping {sec_to_retry:.0f} seconds (approx {sec_to_retry/60:.1f} minutes) until next hourly check mark...")
        time.sleep(sec_to_retry)
        
        check_and_train_assets()

if __name__ == "__main__":
    main()
