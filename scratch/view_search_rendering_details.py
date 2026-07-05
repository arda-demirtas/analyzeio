with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(2515, 2630):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/search_render_details.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Search render details written to scratch/search_render_details.txt")
