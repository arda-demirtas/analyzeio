with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer("prediction_status", content)]
output = []
for m in matches:
    start = max(0, m - 200)
    end = min(len(content), m + 300)
    output.append(f"--- MATCH ---\n{content[start:end]}\n")

with open("c:/Users/h1z1a/Desktop/Analyzeio/scratch/prediction_ui_output.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Output written to scratch/prediction_ui_output.txt")
