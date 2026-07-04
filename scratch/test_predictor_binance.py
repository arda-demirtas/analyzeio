import os
os.environ["DATABASE_URL"] = "postgresql://analyzeio_user:p%40ssword_analyze_io_99@localhost/analyzeio"

from backend.predictor import get_prediction

print("Testing 1d prediction...")
res_1d = get_prediction("BTC-USD", "1d", model_type="xgboost")
hist_1d = res_1d.get("history", [])
print(f"1d history length: {len(hist_1d)}")
if len(hist_1d) > 0:
    print(f"1d last point stoch_k: {hist_1d[-1].get('stoch_k')}")
    print(f"1d last point atr: {hist_1d[-1].get('atr')}")

print("\nTesting 1h prediction...")
res_1h = get_prediction("BTC-USD", "1h", model_type="xgboost")
hist_1h = res_1h.get("history", [])
print(f"1h history length: {len(hist_1h)}")
if len(hist_1h) > 0:
    print(f"1h last point stoch_k: {hist_1h[-1].get('stoch_k')}")
    print(f"1h last point atr: {hist_1h[-1].get('atr')}")
