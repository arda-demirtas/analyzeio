with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "FEATURES =" in line or "DEFAULT_SEQUENCE_LENGTH" in line:
        print(f"Line {idx+1}: {line.strip()}")
