with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(30, 80):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/predict_asset_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved lines to scratch/predict_asset_inspect.txt")
