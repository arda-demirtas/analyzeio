with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "const [modeltype" in line.lower():
        print(f"Line {idx+1}: {line.strip()}")
