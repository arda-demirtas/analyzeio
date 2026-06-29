import os
import sys
import time
import datetime
import traceback

# Ensure parent directory is in python path if run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predictor import get_prediction
from backend.config import MODEL_CACHE_DIR

POPULAR_CRYPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", 
    "SHIB-USD", "DOT-USD", "LINK-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "UNI-USD", "MATIC-USD", 
    "ICP-USD", "ETC-USD", "FIL-USD", "XLM-USD", "HBAR-USD", "ATOM-USD", "APT-USD", "VET-USD", 
    "RNDR-USD", "PEPE-USD", "OP-USD", "STX-USD", "GRT-USD", "LDO-USD", "INJ-USD", "THETA-USD", 
    "IMX-USD", "EGLD-USD", "FTM-USD", "ALGO-USD", "MKR-USD", "FLOW-USD", "MNT-USD", "AAVE-USD", 
    "SEI-USD", "AR-USD", "WIF-USD", "BONK-USD", "FLOKI-USD", "QNT-USD", "GALA-USD", "MANA-USD", 
    "AXS-USD", "SAND-USD", "JUP-USD", "PYTH-USD", "CHZ-USD", "DYDX-USD", "ENS-USD", "LRC-USD", 
    "ONE-USD", "CRO-USD", "TIA-USD", "MINA-USD"
]

def check_and_train_crypto():
    """Runs daily model training sequentially for the popular cryptos list."""
    print(f"\n[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Starting Daily Crypto Auto-Training loop...")
    success_count = 0
    fail_count = 0
    
    for idx, symbol in enumerate(POPULAR_CRYPTOS):
        try:
            print(f"[{idx+1}/{len(POPULAR_CRYPTOS)}] Training/Updating cache for {symbol} (1d)...")
            get_prediction(symbol, interval="1d")
            success_count += 1
        except Exception as e:
            print(f"Error training {symbol}: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print(f"[{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Crypto training cycle completed. Success: {success_count}, Failed: {fail_count}")

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
    print("Crypto Daily Auto-Training Daemon Started!")
    print("====================================================")
    
    # 1. Warm up cache immediately on startup (for missing or stale models)
    check_and_train_crypto()
    
    # 2. Main sleep-and-run loop
    while True:
        sleep_sec = get_seconds_until_next_run()
        next_run_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=sleep_sec)
        print(f"Sleeping for {sleep_sec:.0f} seconds (approx {sleep_sec/3600:.2f} hours) until next scheduled run at {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} UTC...")
        time.sleep(sleep_sec)
        
        # Trigger training
        check_and_train_crypto()

if __name__ == "__main__":
    main()
