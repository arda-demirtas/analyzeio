from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, Watchlist
from backend.schemas import WatchlistAdd, WatchlistResponse, PredictionResponse
from backend.auth import get_current_user
from backend.predictor import get_prediction

router = APIRouter(prefix="/api", tags=["Predictions & Watchlist"])

@router.get("/predict", response_model=PredictionResponse)
def predict_asset(symbol: str, current_user: User = Depends(get_current_user)):
    """
    Triggers historical data loading, computes technical indicators,
    and runs LSTM model inference to predict the next day's close price.
    """
    symbol_upper = symbol.upper().strip()
    try:
        prediction_result = get_prediction(symbol_upper)
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
    symbol_upper = data.symbol.upper().strip()
    
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
    symbol_upper = symbol.upper().strip()
    
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
