with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

line_num = -1
for idx, line in enumerate(lines):
    if "chart_indicators" in line and "glass-panel" in lines[idx-1]:
        line_num = idx
        break

print(f"Found chart_indicators on line: {line_num+1}")

output = []
if line_num != -1:
    for idx in range(line_num - 2, line_num + 20):
        if idx < len(lines):
            output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/shifted_indicator_layout.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Shifted layout written to scratch/shifted_indicator_layout.txt")
