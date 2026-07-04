with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

line_num = -1
for idx, line in enumerate(lines):
    if "priceChartRef" in line and "useRef" in line:
        line_num = idx
        break

print(f"Found priceChartRef on line: {line_num+1}")

output = []
if line_num != -1:
    for idx in range(line_num - 5, line_num + 20):
        if idx < len(lines):
            output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/ref_lines.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Ref lines written to scratch/ref_lines.txt")
