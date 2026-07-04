with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "activeHistory" in line:
        output.append(f"Line {idx+1}: {line}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/active_history.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("activeHistory references written to scratch/active_history.txt")
