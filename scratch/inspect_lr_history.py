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
import requests

try:
    r = requests.get('http://127.0.0.1:8000/api/predict?symbol=BTC-USD&interval=1d&lang=tr&model_type=xgboost', timeout=30)
    data = r.json()
    history = data.get('history', [])
    print("History length:", len(history))
    
    # Check if lr_predicted_close is populated in history points
    populated = [h for h in history if h.get('lr_predicted_close') is not None]
    print("Populated LR history points:", len(populated))
    if len(populated) > 0:
        print("First populated point:", populated[0])
        print("Last populated point:", populated[-1])
except Exception as e:
    print('Request failed:', e)
"""

ssh.exec_command("cat > /tmp/inspect_lr_history.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/inspect_lr_history.py")
print(out)
ssh.close()
