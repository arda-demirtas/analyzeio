with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Search for const renderCharts = in page.js
line_num = -1
for idx, line in enumerate(lines):
    if "const renderCharts =" in line:
        line_num = idx
        break

print(f"Found const renderCharts = on line: {line_num+1}")

output = []
if line_num != -1:
    for idx in range(line_num, line_num + 300):
        if idx < len(lines):
            output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/render_charts_code.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("renderCharts code written to scratch/render_charts_code.txt")
