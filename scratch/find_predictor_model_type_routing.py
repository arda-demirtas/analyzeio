with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(374, 405):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
