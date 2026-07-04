with open("c:/Users/h1z1a/Desktop/Analyzeio/frontend/src/app/page.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Model Prediction Prices" in line or "model_prediction_prices" in line or "Prediction Prices" in line:
        print(f"Line {idx+1}: {line.strip()}")
