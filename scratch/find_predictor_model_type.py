with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "model_type" in line or "predicted_close =" in line:
        output.append(f"Line {idx+1}: {line}")
        # Print context
        start = max(0, idx - 3)
        end = min(len(lines), idx + 8)
        output.append("Context:")
        for c_idx in range(start, end):
            output.append(f"  {c_idx+1}: {lines[c_idx]}")
        output.append("---\n")

with open("scratch/predictor_model_type.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Predictor model_type refs written to scratch/predictor_model_type.txt")
