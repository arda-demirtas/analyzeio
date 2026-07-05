with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if 'placeholder={t("search_placeholder")}' in line or "placeholder=" in line:
        output.append(f"Line {idx+1}: {line}")
        start = max(0, idx - 5)
        end = min(len(lines), idx + 20)
        output.append("Context:")
        for c_idx in range(start, end):
            output.append(f"  {c_idx+1}: {lines[c_idx]}")
        output.append("---\n")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/all_search_inputs.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("All search inputs written to scratch/all_search_inputs.txt")
