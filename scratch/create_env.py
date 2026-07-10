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
NEXT_PUBLIC_PADDLE_PRICE_STARTER_MONTH=pri_starter_monthly_dummy
NEXT_PUBLIC_PADDLE_PRICE_STARTER_YEAR=pri_starter_yearly_dummy
NEXT_PUBLIC_PADDLE_PRICE_PRO_MONTH=pri_pro_monthly_dummy
NEXT_PUBLIC_PADDLE_PRICE_PRO_YEAR=pri_pro_yearly_dummy
NEXT_PUBLIC_PADDLE_PRICE_ADVANCED_MONTH=pri_advanced_monthly_dummy
NEXT_PUBLIC_PADDLE_PRICE_ADVANCED_YEAR=pri_advanced_yearly_dummy
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
