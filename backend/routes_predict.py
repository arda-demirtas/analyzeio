from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, Watchlist, PredictionLog
from backend.schemas import WatchlistAdd, WatchlistResponse, PredictionResponse, IndicatorPoint, PredictionLogResponse
from backend.auth import get_current_user
from backend.predictor import get_prediction, fetch_interval_history

router = APIRouter(prefix="/api", tags=["Predictions & Watchlist"])

def normalize_symbol(symbol: str) -> str:
    """Normalizes symbol to match Yahoo Finance patterns, e.g., mapping USDT -> USD for crypto."""
    sym = symbol.upper().strip()
    if sym.endswith("-USDT"):
        sym = sym[:-5] + "-USD"
    elif sym.endswith("USDT"):
        sym = sym[:-4] + "-USD"
    elif sym.endswith("USD") and not sym.endswith("-USD") and not sym.endswith(".X"):
        if len(sym) > 3 and not "=" in sym:
            sym = sym[:-3] + "-USD"
    return sym

@router.get("/predict", response_model=PredictionResponse)
def predict_asset(symbol: str, interval: str = "1d", lang: str = "en", current_user: User = Depends(get_current_user)):
    """
    Triggers historical data loading, computes technical indicators,
    and runs LSTM model inference to predict the close price for the next candle of the selected interval.
    """
    symbol_upper = normalize_symbol(symbol)
    if interval not in ["15m", "1h", "4h", "1d"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported interval. Allowed: 15m, 1h, 4h, 1d"
        )
    if not current_user.is_premium and interval != "1d":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Intervals other than 1d are restricted to Premium members."
        )
    try:
        prediction_result = get_prediction(symbol_upper, interval=interval, lang=lang)
        return prediction_result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing model prediction: {str(err)}"
        )

@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns all watchlist assets for the current user."""
    return current_user.watchlist_items

@router.post("/watchlist", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(data: WatchlistAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Adds a ticker symbol to the user's watchlist."""
    symbol_upper = normalize_symbol(data.symbol)
    
    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol_upper
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol already in your watchlist"
        )
        
    watchlist_item = Watchlist(user_id=current_user.id, symbol=symbol_upper)
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    return watchlist_item

@router.delete("/watchlist/{symbol}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(symbol: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remains a ticker symbol from the user's watchlist."""
    symbol_upper = normalize_symbol(symbol)
    
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol_upper
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symbol not found in your watchlist"
        )
        
    db.delete(item)
    db.commit()
    return {"message": f"{symbol_upper} removed from watchlist"}

@router.get("/predictions/accuracy/{symbol}", response_model=List[PredictionLogResponse])
def get_prediction_accuracy_logs(
    symbol: str,
    interval: str = "1d",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the logs of all predictions made for the symbol,
    along with actual closes if they have resolved.
    """
    symbol_upper = normalize_symbol(symbol)
    logs = (
        db.query(PredictionLog)
        .filter(PredictionLog.symbol == symbol_upper, PredictionLog.interval == interval)
        .order_by(PredictionLog.prediction_date.desc())
        .limit(30)
        .all()
    )
    return logs
