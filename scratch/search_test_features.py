with open("c:/Users/h1z1a/Desktop/Analyzeio/backend/tests/test_backend.py", "r", encoding="utf-8") as f:
    content = f.read()

if "FEATURES" in content:
    print("Found FEATURES in test_backend.py")
    for idx, line in enumerate(content.split("\n")):
        if "FEATURES" in line:
            print(f"  Line {idx+1}: {line.strip()}")
else:
    print("Not found in test_backend.py")
