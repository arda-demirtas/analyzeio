with open("backend/predictor.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"seq_length\s*=", content)]
print(f"Found {len(matches)} occurrences")

output = []
for m in matches:
    start = max(0, m - 50)
    end = min(len(content), m + 150)
    output.append(f"Position {m}:\n{content[start:end]}\n---")

with open("scratch/seq_length_def.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Results written to scratch/seq_length_def.txt")
