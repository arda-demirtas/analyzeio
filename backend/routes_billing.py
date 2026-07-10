import hmac
import hashlib
import json
import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Customer, Subscription
from backend.auth import get_current_user
import requests

router = APIRouter(prefix="/api", tags=["Billing & Subscriptions"])

def verify_paddle_signature(raw_body: bytes, header: str, secret_key: str) -> bool:
    """Verifies that the webhook payload was sent by Paddle using HMAC-SHA256."""
    if not header or not secret_key:
        return False
    try:
        parts = {}
        for item in header.split(';'):
            if '=' in item:
                k, v = item.split('=', 1)
                parts[k.strip()] = v.strip()
        timestamp = parts.get('ts')
        signature = parts.get('h1')
        if not timestamp or not signature:
            return False
    except Exception:
        return False
    
    # Construct signed message format: timestamp:raw_body
    message = f"{timestamp}:".encode() + raw_body
    
    # Compute HMAC signature
    computed_sig = hmac.new(
        secret_key.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_sig, signature)


def check_premium_access(email: str, db: Session) -> bool:
    """Access helper: determines if user currently has paid access.
    Treats 'active' and 'trialing' as access-granting.
    """
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        return False
    
    active_sub = db.query(Subscription).filter(
        Subscription.customer_id == customer.customer_id,
        Subscription.status.in_(["active", "trialing"])
    ).first()
    
    return active_sub is not None


@router.post("/webhooks/paddle", status_code=status.HTTP_200_OK)
async def handle_paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """Receives, verifies, and routes Paddle webhook events."""
    raw_body = await request.body()
    signature_header = request.headers.get("Paddle-Signature")
    
    # Determine the signing secret based on current environment
    paddle_env = os.environ.get("NEXT_PUBLIC_PADDLE_ENV", "sandbox")
    if paddle_env == "production":
        secret_key = os.environ.get("PADDLE_LIVE_WEBHOOK_SECRET")
    else:
        secret_key = os.environ.get("PADDLE_SANDBOX_WEBHOOK_SECRET")
        
    if not secret_key:
        # Fallback to general webhook secret env if specific ones are not set
        secret_key = os.environ.get("PADDLE_WEBHOOK_SECRET")

    # 1. Signature Verification (Fail loudly / return non-2xx if invalid)
    if not verify_paddle_signature(raw_body, signature_header, secret_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Webhook signature verification failed"
        )
        
    try:
        payload = json.loads(raw_body.decode('utf-8'))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
        
    event_type = payload.get("event_type")
    event_data = payload.get("data", {})
    
    # 2. Event Routing (Idempotent upsert handlers)
    if event_type in ["customer.created", "customer.updated"]:
        customer_id = event_data.get("id")
        email = event_data.get("email")
        
        if customer_id and email:
            # Idempotent upsert
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                customer = Customer(customer_id=customer_id)
                db.add(customer)
            customer.email = email
            customer.updated_at = datetime.datetime.utcnow()
            db.commit()
            
    elif event_type in ["subscription.created", "subscription.updated", "subscription.canceled"]:
        subscription_id = event_data.get("id")
        customer_id = event_data.get("customer_id")
        status_val = event_data.get("status")
        
        # Extract first price/product item
        items = event_data.get("items", [])
        price_id = ""
        product_id = ""
        if items:
            price_obj = items[0].get("price", {})
            price_id = price_obj.get("id", "")
            product_id = price_obj.get("product_id", "")
            
        # Extract scheduled change
        scheduled_change = event_data.get("scheduled_change")
        change_action = None
        change_at = None
        if scheduled_change:
            change_action = scheduled_change.get("action")
            change_at_str = scheduled_change.get("effective_at")
            if change_at_str:
                try:
                    change_at = datetime.datetime.fromisoformat(change_at_str.replace("Z", "+00:00"))
                except Exception:
                    pass
                    
        if subscription_id and customer_id and status_val:
            # Idempotent upsert
            sub = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()
            if not sub:
                sub = Subscription(subscription_id=subscription_id)
                db.add(sub)
            sub.customer_id = customer_id
            sub.status = status_val
            sub.price_id = price_id
            sub.product_id = product_id
            sub.scheduled_change_action = change_action
            sub.scheduled_change_at = change_at
            sub.updated_at = datetime.datetime.utcnow()
            db.commit()
            
            # Sync user's premium status
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if customer:
                user = db.query(User).filter(User.email == customer.email).first()
                if user:
                    # Update is_premium based on subscription status helper
                    user.is_premium = check_premium_access(customer.email, db)
                    db.commit()
                    
    return {"status": "success", "event_type": event_type}


@router.post("/billing/portal-session")
def create_customer_portal_session(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Mints a Paddle customer portal session for the authenticated user."""
    # 1. Resolve their Paddle customer record
    customer = db.query(Customer).filter(Customer.email == current_user.email).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Paddle customer account found. Please subscribe to a plan first."
        )
        
    # 2. Gather active subscription IDs
    subs = db.query(Subscription).filter(Subscription.customer_id == customer.customer_id).all()
    subscription_ids = [s.subscription_id for s in subs]
    
    # 3. Read API config
    paddle_env = os.environ.get("NEXT_PUBLIC_PADDLE_ENV", "sandbox")
    if paddle_env == "production":
        api_key = os.environ.get("PADDLE_LIVE_API_KEY")
        base_url = "https://api.paddle.com"
    else:
        api_key = os.environ.get("PADDLE_SANDBOX_API_KEY")
        base_url = "https://sandbox-api.paddle.com"
        
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Paddle API key is not configured on the server."
        )
        
    # 4. Request portal session from Paddle API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "subscription_ids": subscription_ids
    }
    
    url = f"{base_url}/customers/{customer.customer_id}/portal-sessions"
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code not in [200, 201]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paddle API returned error: {r.status_code} - {r.text}"
            )
        data = r.json()
        overview_url = data.get("data", {}).get("urls", {}).get("general", {}).get("overview")
        if not overview_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Paddle API response did not include a portal overview URL."
            )
        return {"url": overview_url}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error minting portal session: {str(e)}"
        )
