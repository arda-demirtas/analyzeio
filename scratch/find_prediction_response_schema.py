with open("backend/schemas.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "class PredictionResponse" in line:
        print(f"Starts at line {idx+1}")
        for context_idx in range(idx, idx + 30):
            print(f"  {context_idx+1}: {lines[context_idx].rstrip()}")
        break
