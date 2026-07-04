with open("backend/data_fetcher.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [m.start() for m in re.finditer(r"stoch_k|atr|obv|cci|williams_r", content, re.IGNORECASE)]
print(f"Found {len(matches)} matches in backend/data_fetcher.py")

output = []
for m in matches:
    start = max(0, m - 100)
    end = min(len(content), m + 200)
    output.append(f"Position {m}:\n{content[start:end]}\n---")

with open("scratch/data_fetcher_indicators_inspect.txt", "w", encoding="utf-8") as f_out:
    f_out.writelines("\n".join(output))

print("Results written to scratch/data_fetcher_indicators_inspect.txt")
