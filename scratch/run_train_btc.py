import sys
import os

# Add parent directory of scratch to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predictor import get_prediction

print("Starting force train for BTC-USD on VPS...")
try:
    res = get_prediction('BTC-USD', interval='1d', force_retrain=True, is_daemon=True)
    print("SUCCESS!")
    print("Keys trained:", list(res.keys()))
    print("sr_predicted_close:", res.get('sr_predicted_close'))
    print("sr_metrics:", res.get('sr_metrics'))
except Exception as e:
    print("Error during training:", e)
