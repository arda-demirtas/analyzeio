with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "history_list" in line or "stoch_k" in line:
        output.append(f"Line {idx+1}: {line}")

with open("scratch/predictor_history.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Predictor history references written to scratch/predictor_history.txt")
