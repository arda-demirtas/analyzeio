import subprocess
import os

def main():
    print("Running PM2 cleanup and startup script...")
    
    # 1. Kill all running PM2 daemons
    print("Killing existing PM2 processes...")
    subprocess.run(["pm2", "kill"])
    
    # 2. Run env creation
    print("Creating .env file...")
    subprocess.run(["venv/bin/python", "scratch/create_env.py"])
    
    # 3. Start backend
    print("Starting backend PM2 process...")
    subprocess.run(["pm2", "start", "venv/bin/python", "--name", "backend", "--", "-m", "backend.main"])
    
    # 4. Start crypto-daemon
    print("Starting crypto-daemon PM2 process...")
    subprocess.run(["pm2", "start", "venv/bin/python", "--name", "crypto-daemon", "--", "-m", "backend.crypto_daemon"])
    
    print("\nPM2 initialization completed successfully!")

if __name__ == "__main__":
    main()
