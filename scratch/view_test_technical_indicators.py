with open("c:/Users/h1z1a/Desktop/Analyzeio/backend/tests/test_backend.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

started = False
for idx, line in enumerate(lines):
    if "def test_technical_indicators" in line:
        started = True
    if started:
        print(f"Line {idx+1}: {line.strip()}")
        if "def " in line and not "test_technical_indicators" in line:
            break
