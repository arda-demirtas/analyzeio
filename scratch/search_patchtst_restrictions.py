with open("backend/predictor.py", "r", encoding="utf-8") as f:
    text_pred = f.read()

with open("backend/routes_predict.py", "r", encoding="utf-8") as f:
    text_routes = f.read()

print("PatchTST in predictor.py:", "BTC" in text_pred)
print("PatchTST in routes_predict.py:", "BTC" in text_routes)
