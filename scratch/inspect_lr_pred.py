import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.59.232", username="root", password="Taktakshow123*", timeout=10)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd)
    return (stdout.read() + stderr.read()).decode("utf-8", errors="replace")

py_code = """
import sys
sys.path.append("/var/www/analyzeio")
import pickle, os, json, datetime
import pandas as pd
import numpy as np
from backend.predictor import fetch_market_data, FEATURES, DEFAULT_SEQUENCE_LENGTH
from backend.config import MODEL_CACHE_DIR

symbol = "BTC-USD"
interval = "1d"
seq_length = DEFAULT_SEQUENCE_LENGTH

df, name, _, _ = fetch_market_data(symbol, interval=interval)
last_close = float(df["Close"].iloc[-1])

print("Total rows in df on VPS:", len(df))
if len(df) > 0:
    print("First date:", df.index[0])
    print("Last date:", df.index[-1])

cache_path_lr = os.path.join(MODEL_CACHE_DIR, f"{symbol}_{interval}_model_lr.pkl")
with open(cache_path_lr, "rb") as f:
    model_lr = pickle.load(f)

# Inspect inputs
last_features_lr = df[FEATURES].iloc[-seq_length:].values.flatten().reshape(1, -1)
predicted_lr_return = float(model_lr.predict(last_features_lr)[0])
predicted_close = float(last_close * (1 + predicted_lr_return))

print("last_close:", last_close)
print("predicted_lr_return:", predicted_lr_return)
print("predicted_close:", predicted_close)
print("model coefs shape:", model_lr.coef_.shape)
print("model intercept:", model_lr.intercept_)
print("last_features_lr min/max:", np.min(last_features_lr), np.max(last_features_lr))
"""

ssh.exec_command("cat > /tmp/inspect_lr.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/inspect_lr.py")
print(out)
ssh.close()
