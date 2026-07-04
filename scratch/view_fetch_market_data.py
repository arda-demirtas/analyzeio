with open("backend/data_fetcher.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for idx in range(120, 220):
    if idx < len(lines):
        output.append(f"Line {idx+1}: {lines[idx]}")

with open("scratch/view_fetch_market_data.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines(output)

print("view_fetch_market_data code written to scratch/view_fetch_market_data.txt")
