with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(414, 460):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
