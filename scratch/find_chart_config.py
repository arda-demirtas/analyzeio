with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "datasets:" in line or "hidden:" in line:
        print(f"Line {idx+1}: {line.strip()}")
