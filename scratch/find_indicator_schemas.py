with open("backend/schemas.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"class\s+IndicatorPoint|class\s+PredictionResponse", content)]
print(f"Found {len(matches)} matches")

output = []
for m in matches:
    start = max(0, m - 50)
    end = min(len(content), m + 800)
    output.append(f"Position {m}:\n{content[start:end]}\n---")

with open("scratch/indicator_schemas_output.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Results written to scratch/indicator_schemas_output.txt")
