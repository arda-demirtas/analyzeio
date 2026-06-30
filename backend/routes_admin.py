from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from typing import List

from backend.database import get_db
from backend.models import User
from backend.auth import get_current_user
from backend.predictor import MODEL_CACHE_DIR

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.email != "arda.demirtas2002@gmail.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrators only."
        )
    return current_user

@router.get("/users")
def get_users(db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "is_premium": u.is_premium,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

@router.post("/users/{user_id}/toggle-premium")
def admin_toggle_premium(user_id: int, db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user.is_premium = not user.is_premium
    db.commit()
    db.refresh(user)
    return {"status": "success", "is_premium": user.is_premium}

@router.get("/system-stats")
def get_system_stats(db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    total_users = db.query(User).count()
    premium_users = db.query(User).filter(User.is_premium == True).count()
    
    model_files = []
    if os.path.exists(MODEL_CACHE_DIR):
        model_files = [f for f in os.listdir(MODEL_CACHE_DIR) if f.endswith(".keras")]
        
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_cached_models": len(model_files),
        "cached_models": sorted(model_files)
    }
