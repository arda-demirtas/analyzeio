with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(75, 420):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/get_prediction_flow_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved lines to scratch/get_prediction_flow_inspect.txt")
