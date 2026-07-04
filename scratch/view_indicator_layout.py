with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Search for rsi_title inside the code
line_num = -1
for idx, line in enumerate(lines):
    if "rsi_title" in line:
        line_num = idx
        break

print(f"Found rsi_title on line: {line_num+1}")

output = []
if line_num != -1:
    for idx in range(line_num - 30, line_num + 90):
        if idx < len(lines):
            output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/indicator_layout.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Indicator layout written to scratch/indicator_layout.txt")
