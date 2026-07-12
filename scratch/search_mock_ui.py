import sys
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"c:\Users\h1z1a\Desktop\Analyzeio\frontend\src\app\page.js"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

matches = []
for idx, line in enumerate(lines):
    if "mocktradingstate" in line.lower():
        matches.append((idx + 1, line.strip()))

print(f"Found {len(matches)} occurrences of 'mockTradingState':")
for line_no, content in matches:
    print(f"  L{line_no}: {content[:140]}")
