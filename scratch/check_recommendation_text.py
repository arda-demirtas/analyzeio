import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("89.19.22.148", username="root", password="p@ssword_analyze_io_99")

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return (stdout.read() + stderr.read()).decode("utf-8", errors="replace")

py_code = """
import sys
sys.path.append("/var/www/analyzeio")
from backend.predictor import get_prediction

res = get_prediction("ETH-USD", interval="1d", model_type="xgboost", is_daemon=True, lang="tr")
print("Signal:", res.get("technical_recommendation"))
"""

ssh.exec_command("cat > /tmp/check_rec.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/check_rec.py")
print(out)
ssh.close()
