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
from backend.database import SessionLocal
from backend.models import CryptoCandle

db = SessionLocal()
try:
    for symbol in ["BTC-USD", "ETH-USD"]:
        count = db.query(CryptoCandle).filter(CryptoCandle.symbol == symbol, CryptoCandle.interval == "1d").count()
        print(f"{symbol} 1d candles count:", count)
finally:
    db.close()
"""

ssh.exec_command("cat > /tmp/inspect_db.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/inspect_db.py")
print(out)
ssh.close()
