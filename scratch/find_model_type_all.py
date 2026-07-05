with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "modelType" in line:
        output.append(f"Line {idx+1}: {line}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/model_type_all.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("modelType references written to scratch/model_type_all.txt")
