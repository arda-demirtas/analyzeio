import os

search_dir = "c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app"
for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".js") or file.endswith(".jsx") or file.endswith(".ts") or file.endswith(".tsx"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "Historical Price" in content or "Next Day Prediction" in content or "Next Close Prediction" in content:
                    print(f"Found in {path}")
                    for idx, line in enumerate(content.split("\n")):
                        if "Historical Price" in line or "Next Day Prediction" in line or "Next Close Prediction" in line:
                            print(f"  Line {idx+1}: {line.strip()}")
