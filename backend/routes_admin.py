from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from typing import List

from backend.database import get_db
from backend.models import User, AutoTrainSymbol
from backend.auth import get_current_user
from backend.predictor import MODEL_CACHE_DIR
from backend.schemas import AutoTrainSymbolResponse, AutoTrainSymbolAdd

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

@router.get("/auto-train-symbols", response_model=List[AutoTrainSymbolResponse])
def get_auto_train_symbols(db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    return db.query(AutoTrainSymbol).order_by(AutoTrainSymbol.symbol).all()

@router.post("/auto-train-symbols", response_model=AutoTrainSymbolResponse)
def add_auto_train_symbol(payload: AutoTrainSymbolAdd, db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    # Normalize input
    symbol_str = payload.symbol.upper().strip()
    
    # Check if already exists
    existing = db.query(AutoTrainSymbol).filter(AutoTrainSymbol.symbol == symbol_str).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol already exists in auto-train list."
        )
        
    new_sym = AutoTrainSymbol(symbol=symbol_str)
    db.add(new_sym)
    db.commit()
    db.refresh(new_sym)
    return new_sym

@router.delete("/auto-train-symbols/{symbol}")
def delete_auto_train_symbol(symbol: str, db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    symbol_str = symbol.upper().strip()
    target = db.query(AutoTrainSymbol).filter(AutoTrainSymbol.symbol == symbol_str).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symbol not found in auto-train list."
        )
    db.delete(target)
    db.commit()
    return {"status": "success", "message": f"Successfully removed {symbol_str} from auto-train list."}

