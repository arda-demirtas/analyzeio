with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

target_content = "".join(lines[87:375]) # Lines 88 to 375
with open("scratch/target_predictor_flow.txt", "w", encoding="utf-8") as f_out:
    f_out.write(target_content)

print("Target content written to scratch/target_predictor_flow.txt")
