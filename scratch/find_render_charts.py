with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "renderCharts" in line:
        output.append(f"Line {idx+1}: {line}")
        # Print a few lines before and after
        start = max(0, idx - 10)
        end = min(len(lines), idx + 25)
        output.append("Context:")
        for context_idx in range(start, end):
            output.append(f"  {context_idx+1}: {lines[context_idx]}")
        output.append("---\n")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/render_charts_refs.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("renderCharts references written to scratch/render_charts_refs.txt")
