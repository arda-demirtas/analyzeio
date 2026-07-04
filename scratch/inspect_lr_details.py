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
from backend.predictor import fetch_market_data, FEATURES

df, name, _, _ = fetch_market_data("ETH-USD", interval="1h")
print("Total rows:", len(df))
if not df.empty:
    last_row = df[FEATURES].iloc[-1]
    for col in FEATURES:
        print(f"{col}: {last_row[col]}")
else:
    print("DataFrame is empty!")
"""

ssh.exec_command("cat > /tmp/inspect_lr_details.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/inspect_lr_details.py")
print(out)
ssh.close()
