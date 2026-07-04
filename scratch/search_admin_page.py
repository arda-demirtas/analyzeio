with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "admin" in line.lower() or "panel" in line.lower() or "is_admin" in line:
        print(f"Line {idx+1}: {line.strip()}")
