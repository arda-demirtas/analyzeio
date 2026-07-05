with open("frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4045, 4210):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/frontend_patchtst_box_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved lines to scratch/frontend_patchtst_box_inspect.txt")
