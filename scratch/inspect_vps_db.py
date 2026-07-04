import paramiko
import sys

HOST = "46.225.59.232"
USER = "root"
PASSWORD = "Taktakshow123*"

print(f"Connecting to VPS at {HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    print("Connected successfully!")
    
    # Run the inspect script on VPS
    # We will copy inspect_db_candles.py to /var/www/analyzeio/scratch/inspect_db_candles.py first using sftp, or we can just run it inline!
    # Let's use SFTP to upload it first
    sftp = ssh.open_sftp()
    print("Uploading scratch/inspect_db_candles.py to VPS...")
    print("Uploading scratch/test_vps_curl.py to VPS...")
    sftp.put("scratch/test_vps_curl.py", "/var/www/analyzeio/scratch/test_vps_curl.py")
    sftp.close()
    
    print("Running test_vps_curl.py on VPS...")
    cmd = 'cd /var/www/analyzeio && venv/bin/python scratch/test_vps_curl.py'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    
    print("\n--- OUTPUT FROM VPS ---")
    print(out)
    
    if err:
        print("\n--- ERRORS FROM VPS ---")
        print(err)
        
    ssh.close()
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
