with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(1139, 1245):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/chart_rendering_output3.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("chart_rendering part 3 written to scratch/chart_rendering_output3.txt")
