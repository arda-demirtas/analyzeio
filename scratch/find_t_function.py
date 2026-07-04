with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"const t\s*=", content)]
output = []
for m in matches:
    start = max(0, m - 50)
    end = min(len(content), m + 150)
    output.append(f"Position {m}:\n{content[start:end]}\n---")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/t_function_output.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print(f"Found {len(matches)} occurrences. Written to scratch/t_function_output.txt")
