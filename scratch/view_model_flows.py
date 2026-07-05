with open("backend/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
# XGBoost block (approx lines 95-185)
output.append("--- XGBoost Block ---")
for idx in range(95, 185):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

# LSTM block (approx lines 185-260)
output.append("\n--- LSTM Block ---")
for idx in range(185, 260):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

# LR block (approx lines 260-325)
output.append("\n--- LR Block ---")
for idx in range(260, 325):
    if idx < len(lines):
        output.append(f"{idx+1}: {lines[idx]}")

with open("scratch/model_flows_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("Saved model flows to scratch/model_flows_inspect.txt")
