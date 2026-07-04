with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(4245, 4360):
    if idx < len(lines):
        print(f"Line {idx+1}: {lines[idx].rstrip()}")
