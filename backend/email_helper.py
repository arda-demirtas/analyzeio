import smtplib
from email.mime.text import MIMEText
import os
import random

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

def send_verification_email(email: str, code: str, purpose: str) -> bool:
    """
    Sends a verification email to the user with a 6-digit code.
    If SMTP settings are missing, logs it to stdout/stderr so it is readable from logs.
    """
    subject = "Analyzeio - Email Verification"
    if purpose == "register":
        body = f"Welcome to Analyzeio! Your registration verification code is: {code}\nThis code is valid for 15 minutes."
    else:
        body = f"Analyzeio password change request. Your verification code is: {code}\nThis code is valid for 15 minutes."
        
    print(f"\n[VERIFICATION CODE] Sent to {email}: {code} for {purpose}\n")
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[SMTP] SMTP credentials not set. Code printed to logs for local/VPS testing.")
        return True
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = email
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email via SMTP: {e}")
        return False
