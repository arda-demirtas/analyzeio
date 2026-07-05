with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if '"xgb_predicted_close"' in line:
        print(f"Starts at line {idx+1}")
        for context_idx in range(idx - 5, idx + 15):
            print(f"  {context_idx+1}: {lines[context_idx].rstrip()}")
        break
