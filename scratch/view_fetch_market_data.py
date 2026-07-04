with open("c:/Users/h1z1a/Desktop/Analyzeio/backend/data_fetcher.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

started = False
for idx, line in enumerate(lines):
    if "def fetch_market_data" in line:
        started = True
    if started:
        print(f"Line {idx+1}: {line.strip()}")
        if "return " in line and "is_crypto" in line:
            break
