with open("frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4316, 4430):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/comparison_table_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved lines to scratch/comparison_table_inspect.txt")
