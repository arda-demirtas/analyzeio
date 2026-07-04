with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(4504, 4570):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/admin_content_models.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Models content written to scratch/admin_content_models.txt")
