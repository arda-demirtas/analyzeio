with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()
start_printing = False
for idx, line in enumerate(lines):
    if "return {" in line:
        start_printing = True
    if start_printing:
        print(f"{idx+1}: {line}")
        if "}" in line and "    return {" not in line:
            start_printing = False
