with open("frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(198, 215):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
