with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"API_BASE_URL", content)]
print(f"Found {len(matches)} occurrences of API_BASE_URL")

output = []
for m in matches:
    start = max(0, m - 50)
    end = min(len(content), m + 150)
    output.append(f"Position {m}:\n{content[start:end]}\n---")

with open("scratch/api_base_url_output.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Results written to scratch/api_base_url_output.txt")
