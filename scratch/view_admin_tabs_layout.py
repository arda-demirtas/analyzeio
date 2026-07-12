import sys
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"c:\Users\h1z1a\Desktop\Analyzeio\frontend\src\app\page.js"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(5099, min(5200, len(lines))):
    print(f"{idx + 1}: {lines[idx]}", end="")
