import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.59.232", username="root", password="Taktakshow123*", timeout=10)

def run(cmd):
    _, stdout, stderr = ssh.exec_command(cmd)
    return (stdout.read() + stderr.read()).decode("utf-8", errors="replace")

# Force delete old cache
run("rm -f /var/www/analyzeio/model_cache/BTC-USD_1d_model_lr*")

py_code = """
import sys
sys.path.append("/var/www/analyzeio")
import requests

# Get prediction with model_type=linear_regression
try:
    from backend.predictor import get_prediction
    
    # 1. Test ETH-USD
    print("Direct Prediction for ETH-USD...")
    res_eth = get_prediction("ETH-USD", interval="1d", model_type="xgboost", is_daemon=True)
    print("XGBoost prediction:", res_eth.get("xgb_predicted_close"))
    print("XGBoost metrics:", res_eth.get("xgb_metrics"))
    print("LSTM prediction:", res_eth.get("lstm_predicted_close"))
    print("LSTM metrics:", res_eth.get("lstm_metrics"))
    print("Linear Regression prediction:", res_eth.get("lr_predicted_close"))
    print("Linear Regression metrics:", res_eth.get("lr_metrics"))
except Exception as e:
    print('Direct call failed:', e)
"""

ssh.exec_command("cat > /tmp/predict_test_lr.py << 'PYEOF'\n" + py_code + "\nPYEOF")
import time; time.sleep(1)
out = run("cd /var/www/analyzeio && venv/bin/python /tmp/predict_test_lr.py")
print(out)
ssh.close()
