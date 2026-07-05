with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(650, 675):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/useEffect_loadPrediction.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved output to scratch/useEffect_loadPrediction.txt")
