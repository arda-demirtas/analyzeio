with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "triggerSearch" in line:
        output.append(f"Line {idx+1}: {line}")
        # Let's print the function context
        if "const triggerSearch" in line or "function triggerSearch" in line:
            start = max(0, idx - 2)
            end = min(len(lines), idx + 35)
            output.append("Context:")
            for c_idx in range(start, end):
                output.append(f"  {c_idx+1}: {lines[c_idx]}")
            output.append("---\n")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/trigger_search_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("triggerSearch references written to scratch/trigger_search_inspect.txt")
