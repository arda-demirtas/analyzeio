with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "setChartHistory" in line:
        output.append(f"Line {idx+1}: {line}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/chart_history_setter.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Setter code written to scratch/chart_history_setter.txt")
