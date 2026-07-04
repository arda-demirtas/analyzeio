with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4335, 4395):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/admin_tabs_full.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Full tabs snippet written to scratch/admin_tabs_full.txt")
