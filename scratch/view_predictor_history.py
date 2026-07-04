with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(525, 575):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("scratch/view_predictor_history.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("view_predictor_history code written to scratch/view_predictor_history.txt")
