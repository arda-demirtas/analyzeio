import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/translations.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "chart_title:" in line:
        print(f"Line {idx+1}: {line.strip()}")
