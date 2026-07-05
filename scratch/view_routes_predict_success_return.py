with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(85, 138):
    if idx < len(lines):
        print(f"{idx+1}: {lines[idx].rstrip()}")
