with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "metric" in line.lower() or "accuracy" in line.lower() or "rmse" in line.lower():
        if idx > 3300: # only look at layout part
            print(f"Line {idx+1}: {line.strip()}")
