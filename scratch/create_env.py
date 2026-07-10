import os

def main():
    env_path_root = "/var/www/analyzeio/.env"
    env_path_frontend = "/var/www/analyzeio/frontend/.env"
    env_content = """# Environment Variables for Analyzeio
DATABASE_URL=postgresql://analyzeio_user:p%40ssword_analyze_io_99@localhost/analyzeio
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=arda.demirtas2002@gmail.com
SMTP_PASSWORD=zptd oiru hasi wqtz
SMTP_FROM=arda.demirtas2002@gmail.com
JWT_SECRET_KEY=7b9e7d9c8b7f8e7d6c5b4a3b2a1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a
# Paddle Integration Config
NEXT_PUBLIC_PADDLE_ENV=production
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=live_047328e6d9fb470e9ca9284de39
NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_MONTH=pri_01kx6ax011bcdj9mmemjtnxkzc
NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_YEAR=pri_01kx6ax0jgnqtfm786fw6t9b2y
PADDLE_SANDBOX_WEBHOOK_SECRET=pdl_ntf_secret_sandbox_dummy
PADDLE_LIVE_WEBHOOK_SECRET=pdl_ntfset_01kx6b9hjfz1tpafmnxvv1qzay
PADDLE_WEBHOOK_SECRET=pdl_ntfset_01kx6b9hjfz1tpafmnxvv1qzay
PADDLE_SANDBOX_API_KEY=pdl_sb_dummy_key_1234567890abcdef
PADDLE_LIVE_API_KEY=pdl_live_apikey_01kx6aw8xbjyhw46acgvvd1wd3_99983YAtqkpkEJQjSfJY4Y_Au9
"""
    
    print(f"Creating .env files...")
    try:
        with open(env_path_root, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"Successfully created .env at {env_path_root}!")
        
        with open(env_path_frontend, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"Successfully created .env at {env_path_frontend}!")
    except Exception as e:
        print(f"Failed to create .env files: {e}")

if __name__ == "__main__":
    main()
