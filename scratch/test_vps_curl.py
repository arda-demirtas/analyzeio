import urllib.request
import json
import sys

url = "http://localhost:8000/api/predict?symbol=BTC-USD&interval=1d&model_type=xgboost"
print(f"Querying local backend at {url}...")

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
        
    history = data.get("history", [])
    print(f"Received history of length {len(history)}")
    
    if len(history) > 0:
        first_item = history[0]
        last_item = history[-1]
        print("\nFirst item keys and values:")
        for k, v in first_item.items():
            print(f"  {k}: {v}")
        print("\nLast item keys and values:")
        for k, v in last_item.items():
            print(f"  {k}: {v}")
    else:
        print("History is empty!")
except Exception as e:
    print(f"Failed to query backend: {e}")
    sys.exit(1)
