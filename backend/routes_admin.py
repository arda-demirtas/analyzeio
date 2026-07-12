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
    symbols = db.query(AutoTrainSymbol).order_by(AutoTrainSymbol.symbol).all()
    results = []
    import datetime
    for s in symbols:
        cache_path = os.path.join(MODEL_CACHE_DIR, f"{s.symbol}_1d_model.keras")
        last_trained = None
        exists = False
        if os.path.exists(cache_path):
            mtime = os.path.getmtime(cache_path)
            dt = datetime.datetime.fromtimestamp(mtime)
            last_trained = dt.strftime("%Y-%m-%d %H:%M:%S")
            exists = True
            
        results.append({
            "id": s.id,
            "symbol": s.symbol,
            "created_at": s.created_at,
            "last_trained_at": last_trained,
            "is_trained": exists
        })
    return results


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


@router.get("/mock-trading")
def get_admin_mock_trading(admin: User = Depends(check_admin)):
    """Returns the current state of mock trading for admin."""
    from backend.mock_trading import get_mock_trading_state
    return get_mock_trading_state()


@router.post("/mock-trading/reset")
def reset_admin_mock_trading(admin: User = Depends(check_admin)):
    """Resets the mock trading simulation balance to $2000."""
    from backend.mock_trading import save_mock_trading_state, log_mock_event
    import datetime
    reset_state = {
        "balance": 2000.0,
        "position": None,
        "logs": [
            {
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "event": "Mock trading system reset to $2,000.00 cash by Admin."
            }
        ]
    }
    save_mock_trading_state(reset_state)
    return reset_state


@router.get("/predictions-performance")
def get_predictions_performance(db: Session = Depends(get_db), admin: User = Depends(check_admin)):
    """Returns the latest resolved prediction performance for all auto-trained symbols."""
    from backend.models import PredictionLog, AutoTrainSymbol
    from backend.config import AUTO_TRAINED_SYMBOLS
    
    db_symbols = [s.symbol for s in db.query(AutoTrainSymbol).all()]
    symbols = db_symbols if db_symbols else AUTO_TRAINED_SYMBOLS
    
    results = []
    for sym in symbols:
        latest_log = (
            db.query(PredictionLog)
            .filter(
                PredictionLog.symbol == sym,
                PredictionLog.interval == "1d",
                PredictionLog.actual_close != None
            )
            .order_by(PredictionLog.prediction_date.desc())
            .first()
        )
        if latest_log:
            pred_up = latest_log.predicted_close >= 0.5
            actual_up = latest_log.actual_close > latest_log.last_close
            is_correct = pred_up == actual_up
            
            results.append({
                "symbol": latest_log.symbol,
                "prediction_date": latest_log.prediction_date,
                "predicted_close": latest_log.predicted_close,
                "last_close": latest_log.last_close,
                "actual_close": latest_log.actual_close,
                "is_correct": is_correct,
                "predicted_direction": "UP" if pred_up else "DOWN",
                "actual_direction": "UP" if actual_up else "DOWN"
            })
            
    # Calculate stats
    total_evaluated = len(results)
    correct_count = sum(1 for r in results if r["is_correct"])
    accuracy_percent = (correct_count / total_evaluated * 100) if total_evaluated > 0 else 0.0
    bullish_pred_count = sum(1 for r in results if r["predicted_direction"] == "UP")
    bearish_pred_count = sum(1 for r in results if r["predicted_direction"] == "DOWN")
    
    return {
        "stats": {
            "total_evaluated": total_evaluated,
            "correct_count": correct_count,
            "accuracy_percent": round(accuracy_percent, 2),
            "bullish_pred_count": bullish_pred_count,
            "bearish_pred_count": bearish_pred_count
        },
        "details": sorted(results, key=lambda x: x["symbol"])
    }


