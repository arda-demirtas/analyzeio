with open("frontend/src/app/page.js", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
for idx, line in enumerate(lines):
    if "Model Analytics" in line or "Comparison" in line or "comparison" in line or "analytics" in line or "Model Karşılaştırma" in line:
        # Print surrounding context (3 lines before and after)
        print(f"--- Match at line {idx+1} ---")
        start = max(0, idx - 3)
        end = min(len(lines), idx + 4)
        for i in range(start, end):
            print(f"{i+1}: {lines[i]}")
