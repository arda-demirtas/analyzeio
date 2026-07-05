with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if line.startswith("def ") or line.startswith("class "):
        output.append(f"Line {idx+1}: {line.strip()}")

with open("scratch/predictor_helpers.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Predictor helper definitions written to scratch/predictor_helpers.txt")
