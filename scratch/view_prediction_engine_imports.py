with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(14, 25):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
