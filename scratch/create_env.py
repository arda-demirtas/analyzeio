import os

def main():
    env_path = "/var/www/analyzeio/.env"
    env_content = """# Environment Variables for Analyzeio
DATABASE_URL=postgresql://analyzeio_user:p%40ssword_analyze_io_99@localhost/analyzeio
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=arda.demirtas2002@gmail.com
SMTP_PASSWORD=zptd oiru hasi wqtz
SMTP_FROM=arda.demirtas2002@gmail.com
JWT_SECRET_KEY=7b9e7d9c8b7f8e7d6c5b4a3b2a1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a
# Paddle Integration Config
NEXT_PUBLIC_PADDLE_ENV=sandbox
NEXT_PUBLIC_PADDLE_CLIENT_TOKEN=test_dummy_token_value
NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_MONTH=pri_premium_monthly_dummy
NEXT_PUBLIC_PADDLE_PRICE_PREMIUM_YEAR=pri_premium_yearly_dummy
PADDLE_SANDBOX_WEBHOOK_SECRET=pdl_ntf_secret_sandbox_dummy
PADDLE_LIVE_WEBHOOK_SECRET=pdl_ntf_secret_live_dummy
PADDLE_WEBHOOK_SECRET=pdl_ntf_secret_general_dummy
PADDLE_SANDBOX_API_KEY=pdl_sb_dummy_key_1234567890abcdef
PADDLE_LIVE_API_KEY=pdl_live_dummy_key_1234567890abcdef
"""
    
    print(f"Creating .env file at {env_path}...")
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("Successfully created .env file!")
    except Exception as e:
        print(f"Failed to create .env file: {e}")

if __name__ == "__main__":
    main()
