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
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from backend.predictor import fetch_market_data, FEATURES, DEFAULT_SEQUENCE_LENGTH

symbol = "BTC-USD"
interval = "1d"
seq_length = DEFAULT_SEQUENCE_LENGTH

df, name, _, _ = fetch_market_data(symbol, interval=interval)
last_close = float(df["Close"].iloc[-1])

split_idx = int(len(df) * 0.8)
df_train = df.iloc[:split_idx]
df_test = df.iloc[split_idx - seq_length:]

scaler = StandardScaler()
x_train_scaled = scaler.fit_transform(df_train[FEATURES].values)

def make_sequences(x_data, y_data):
    xs, ys = [], []
    for i in range(seq_length, len(x_data)):
        xs.append(x_data[i-seq_length:i])
        ys.append(y_data[i])
    return np.array(xs).reshape(len(xs), -1), np.array(ys)

x_lr_train, y_lr_train = make_sequences(x_train_scaled, df_train["Daily_Return"].values)
model = LinearRegression()
model.fit(x_lr_train, y_lr_train)

last_features_raw = df[FEATURES].iloc[-seq_length:].values
last_features_scaled = scaler.transform(last_features_raw)
last_features = last_features_scaled.flatten().reshape(1, -1)

predicted_lr_return = float(model.predict(last_features)[0])
predicted_close = float(last_close * (1 + predicted_lr_return))

print("last_close:", last_close)
print("predicted_lr_return:", predicted_lr_return)
print("predicted_close:", predicted_close)
"""

ssh.exec_command("cat > /tmp/test_lr_scaled.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/test_lr_scaled.py")
print(out)
ssh.close()
