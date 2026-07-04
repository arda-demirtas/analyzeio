import os
os.environ["DATABASE_URL"] = "postgresql://analyzeio_user:p%40ssword_analyze_io_99@localhost/analyzeio"

from backend.data_fetcher import fetch_interval_history

print("Fetching history...")
history = fetch_interval_history("BTC-USD", "1d")
print(f"Total history length: {len(history)}")

if len(history) > 0:
    last_item = history[-1]
    print("\nKeys in last history item:")
    for k, v in last_item.items():
        print(f"  {k}: {v} (type: {type(v)})")
else:
    print("History is empty!")
