with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(2569, 2605):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/search_render_inspect2.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Search render code part 2 written to scratch/search_render_inspect2.txt")
