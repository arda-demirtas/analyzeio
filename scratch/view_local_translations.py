with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(100, 180):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/local_translations.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Local translations code written to scratch/local_translations.txt")
