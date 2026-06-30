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
        # Stop RAM-heavy services before build to prevent memory locks
        "pm2 stop crypto-daemon || true",
        "pm2 stop frontend || true",
        "sync && echo 3 > /proc/sys/vm/drop_caches",
        
        # 1. Update the git repository (use hard reset to avoid potential local file state issues)
        f"cd {DEST_DIR} && git fetch --all && git reset --hard origin/main",
        
        # Remove old favicon.ico explicitly
        f"rm -f {DEST_DIR}/frontend/src/app/favicon.ico",
        
        # 2. Update python dependencies
        f"cd {DEST_DIR} && venv/bin/pip install -r requirements.txt",
        
        # 3. Run database migrations to prepare tables in PostgreSQL
        f"cd {DEST_DIR} && DATABASE_URL=\"postgresql://analyzeio_user:p@ssword_analyze_io_99@localhost/analyzeio\" venv/bin/python -c \"from backend.database import run_migrations; run_migrations()\"",

        # 4. Update node packages & build frontend
        f"cd {DEST_DIR}/frontend && npm install",
        f"cd {DEST_DIR}/frontend && NODE_OPTIONS='--max-old-space-size=1024' npm run build",
        
        # 5. Recreate PM2 configurations with new environment variables
        "pm2 delete backend || true",
        "pm2 delete crypto-daemon || true",
        f"DATABASE_URL=\"postgresql://analyzeio_user:p@ssword_analyze_io_99@localhost/analyzeio\" pm2 start venv/bin/python --name \"backend\" --cwd {DEST_DIR} -- -m backend.main",
        f"DATABASE_URL=\"postgresql://analyzeio_user:p@ssword_analyze_io_99@localhost/analyzeio\" pm2 start {DEST_DIR}/backend/crypto_daemon.py --name \"crypto-daemon\" --cwd {DEST_DIR} --interpreter {DEST_DIR}/venv/bin/python",
        "pm2 start frontend || pm2 restart frontend",
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
