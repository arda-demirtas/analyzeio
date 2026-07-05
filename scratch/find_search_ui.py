with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "searchMatches" in line or "searchQuery" in line or "handleSearch" in line:
        output.append(f"Line {idx+1}: {line}")
        # Print context if it seems like a container or render block
        if "map" in line or "input" in line or "useState" in line:
            start = max(0, idx - 5)
            end = min(len(lines), idx + 15)
            output.append("Context:")
            for c_idx in range(start, end):
                output.append(f"  {c_idx+1}: {lines[c_idx]}")
            output.append("---\n")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/search_ui_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Search UI references written to scratch/search_ui_inspect.txt")
