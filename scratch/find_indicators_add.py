import os

search_dir = "c:/Users/h1z1a/Desktop/Analyzeio/backend"
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "def" in content and ("indicator" in content.lower() or "prepare" in content.lower() or "fetch" in content.lower()):
                    for line in content.split("\n"):
                        if "def " in line and ("indicator" in line.lower() or "prepare" in line.lower() or "fetch" in line.lower()):
                            print(f"{path}: {line.strip()}")
