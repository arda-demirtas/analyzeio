import os

search_dir = "c:/Users/h1z1a/Desktop/Analyzeio/backend"
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "FEATURES" in content:
                    print(f"Found in {path}")
                    for idx, line in enumerate(content.split("\n")):
                        if "FEATURES" in line:
                            print(f"  Line {idx+1}: {line.strip()}")
