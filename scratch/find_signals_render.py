with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4030, 4110):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/signals_render.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved output to scratch/signals_render.txt")
