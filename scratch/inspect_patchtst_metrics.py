with open("backend/model_patchtst_handler.py", "r", encoding="utf-8") as f:
    text = f.read()

print("get_patchtst_prediction signature / return code snippet:")
lines = text.splitlines()
for idx, line in enumerate(lines):
    if "return" in line:
        print(f"Line {idx+1}: {line.strip()}")
