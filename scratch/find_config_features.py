with open("backend/config.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "FEATURES =" in line or "FEATURES = [" in line:
        print(f"Line {idx+1}")
        for context in range(idx, min(len(lines), idx + 10)):
            print(f"  {context+1}: {lines[context].rstrip()}")
        break
