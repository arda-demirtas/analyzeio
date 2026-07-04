with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(75, 110):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("scratch/seq_length_error.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("seq_length_error code written to scratch/seq_length_error.txt")
