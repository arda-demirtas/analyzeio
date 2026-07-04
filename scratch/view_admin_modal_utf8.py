with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4250, 4450):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/admin_modal_snippet.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Snippet written to scratch/admin_modal_snippet.txt")
