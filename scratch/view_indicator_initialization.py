with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Search for rsiChartInst in page.js
line_num = -1
for idx, line in enumerate(lines):
    if "rsiChartInst.current" in line:
        line_num = idx
        break

print(f"Found rsiChartInst on line: {line_num+1}")

output = []
if line_num != -1:
    for idx in range(line_num - 20, line_num + 140):
        if idx < len(lines):
            output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/indicator_initialization.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Indicator initialization written to scratch/indicator_initialization.txt")
