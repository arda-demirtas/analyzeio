import os
import sys

# Ensure print outputs are encoded correctly
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.predictor import get_prediction

try:
    print("Testing get_prediction for patchtst on BTC-USD...")
    res = get_prediction("BTC-USD", interval="1d", model_type="patchtst")
    print("Result keys:", res.keys())
    print("patchtst_predicted_close:", res.get("patchtst_predicted_close"))
    print("patchtst_metrics:", res.get("patchtst_metrics"))
    print("prediction_status:", res.get("prediction_status"))
    print("prediction_error:", res.get("prediction_error"))
except Exception as e:
    print("Exception occurred:", e)
