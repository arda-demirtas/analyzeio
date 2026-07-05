with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_line = None
end_line = None

for idx, line in enumerate(lines):
    if "if not is_pending_data:" in line:
        if start_line is None:
            start_line = idx + 1
    if "last_row = df.iloc[-1]" in line:
        end_line = idx
        break

print(f"Start Line: {start_line}, End Line: {end_line}")
if start_line and end_line:
    print("Context around start:")
    for idx in range(start_line - 3, start_line + 5):
        print(f"  {idx+1}: {lines[idx].rstrip()}")
    print("Context around end:")
    for idx in range(end_line - 5, end_line + 3):
        print(f"  {idx+1}: {lines[idx].rstrip()}")
