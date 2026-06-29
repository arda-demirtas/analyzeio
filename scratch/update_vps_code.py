import os
import sys
import paramiko

HOST = "46.225.59.232"
USER = "root"
PASSWORD = "Taktakshow123*"
DEST_DIR = "/var/www/analyzeio"

def run_ssh_commands(ssh, commands):
    """Executes a list of commands over SSH, printing output in real time with encoding handling."""
    for cmd in commands:
        print(f"\n---> Running on VPS: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Print output in real time safely
        while True:
            line = stdout.readline()
            if not line:
                break
            try:
                print(f"  [OUT] {line.strip()}")
            except Exception:
                try:
                    enc = sys.stdout.encoding or "utf-8"
                    print(f"  [OUT] {line.strip().encode(enc, errors='replace').decode(enc)}")
                except Exception:
                    print(f"  [OUT] {line.strip().encode('ascii', errors='replace').decode('ascii')}")
            
        # Print errors safely
        err = stderr.read().decode("utf-8")
        if err:
            try:
                print(f"  [ERR] {err.strip()}")
            except Exception:
                try:
                    enc = sys.stdout.encoding or "utf-8"
                    print(f"  [ERR] {err.strip().encode(enc, errors='replace').decode(enc)}")
                except Exception:
                    print(f"  [ERR] {err.strip().encode('ascii', errors='replace').decode('ascii')}")
            
        # Check exit status
        status = stdout.channel.recv_exit_status()
        print(f"---> Exit Status: {status}")
        if status != 0:
            print("[ERROR] Command failed. Stopping update.")
            return False
    return True

def main():
    print(f"Connecting to VPS at {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
        print("Connected successfully!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)
        
    commands = [
        # 1. Update the git repository (use hard reset to avoid potential local file state issues)
        f"cd {DEST_DIR} && git fetch --all && git reset --hard origin/main",
        
        # Remove old favicon.ico explicitly
        f"rm -f {DEST_DIR}/frontend/src/app/favicon.ico",
        
        # 2. Update python dependencies
        f"cd {DEST_DIR} && venv/bin/pip install -r requirements.txt",
        

        # 3. Update node packages & build frontend
        f"cd {DEST_DIR}/frontend && npm install",
        f"cd {DEST_DIR}/frontend && npm run build",
        
        # 4. Restart pm2 services
        "pm2 restart all",
        f"pm2 describe crypto-daemon > /dev/null && pm2 restart crypto-daemon || pm2 start {DEST_DIR}/backend/crypto_daemon.py --name \"crypto-daemon\" --interpreter {DEST_DIR}/venv/bin/python",
        "pm2 status"
    ]
    
    success = run_ssh_commands(ssh, commands)
    ssh.close()
    
    if success:
        print("\n==============================================")
        print("VPS CODE UPDATE AND RESTART SUCCESSFUL!")
        print("==============================================")
    else:
        print("\n==============================================")
        print("VPS UPDATE FAILED. Please review the errors.")
        print("==============================================")

if __name__ == "__main__":
    main()
