with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(1400, 1450):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/api_predict.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("api_predict code written to scratch/api_predict.txt")
