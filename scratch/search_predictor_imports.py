with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx, line in enumerate(lines):
    if "import" in line:
        output.append(f"Line {idx+1}: {line.strip()}")

with open("scratch/predictor_imports.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Predictor imports written to scratch/predictor_imports.txt")
