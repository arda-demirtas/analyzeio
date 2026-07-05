with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "searchQuery" in line and "useEffect" in line:
        output.append(f"Line {idx+1}: {line}")
    if "triggerSearch" in line and "useEffect" in line:
        output.append(f"Line {idx+1}: {line}")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/search_query_watch.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Search watch references written to scratch/search_query_watch.txt")
