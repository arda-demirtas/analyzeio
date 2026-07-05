with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "get_prediction" in line:
        output.append(f"Line {idx+1}: {line}")
        # Print surrounding lines
        start = max(0, idx - 5)
        end = min(len(lines), idx + 25)
        output.append("Context:")
        for c_idx in range(start, end):
            output.append(f"  {c_idx+1}: {lines[c_idx]}")
        output.append("---\n")

with open("scratch/predict_route_return.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Predict route return lines written to scratch/predict_route_return.txt")
