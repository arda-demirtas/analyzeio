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

# Get prediction with model_type=linear_regression
try:
    r = requests.get('http://127.0.0.1:8000/api/predict?symbol=BTC-USD&interval=1d&lang=tr&model_type=linear_regression', timeout=30)
    print('Status Code:', r.status_code)
    data = r.json()
    print('Predicted Close:', data.get('predicted_close'))
    print('Model Type:', data.get('model_type'))
    print('Metrics:', data.get('metrics'))
except Exception as e:
    print('Request failed:', e)
"""

ssh.exec_command("cat > /tmp/predict_test_lr.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/predict_test_lr.py")
print(out)
ssh.close()
