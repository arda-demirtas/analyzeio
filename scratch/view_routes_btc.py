with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "BTC" in line:
        print(f"Line {idx+1}: {line.strip()}")
