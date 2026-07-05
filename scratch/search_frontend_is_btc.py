import os

def search_files(directory):
    for root, dirs, files in os.walk(directory):
        if "node_modules" in root or ".next" in root:
            continue
        for file in files:
            if file.endswith((".js", ".jsx", ".ts", ".tsx")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "patchtst" in content.lower() or "isbtcsymbol" in content.lower() or "isbtc" in content.lower():
                        lines = content.splitlines()
                        for idx, line in enumerate(lines):
                            if "patchtst" in line.lower() or "isbtcsymbol" in line or "isbtc" in line.lower():
                                print(f"{filepath} Line {idx+1}: {line.strip()}")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

search_files("frontend")
