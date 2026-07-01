from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import User, Watchlist, PredictionLog, MarketScreener
from backend.schemas import (
    WatchlistAdd, WatchlistResponse, PredictionResponse, IndicatorPoint, 
    PredictionLogResponse, MarketScreenerResponse, NewsSentimentResponse
)
from backend.auth import get_current_user, get_current_user_optional
from backend.predictor import get_prediction, fetch_interval_history, fetch_symbol_news

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
def predict_asset(symbol: str, interval: str = "1d", lang: str = "en", current_user: Optional[User] = Depends(get_current_user_optional)):
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
    is_btc = symbol_upper == "BTC-USD"
    is_premium = current_user.is_premium if current_user else False
    if not is_premium and not is_btc:
        try:
            history_points = fetch_interval_history(symbol_upper, interval=interval)
            if not history_points:
                raise ValueError("No historical points returned")
            last_point = history_points[-1]
            
            from backend.predictor import TICKER_NAMES
            name = TICKER_NAMES.get(symbol_upper, symbol_upper)
            current_price = last_point["close"]
                
            return {
                "symbol": symbol_upper,
                "name": name,
                "last_date": last_point["date"],
                "last_close": last_point["close"],
                "predicted_close": None,
                "prediction_date": None,
                "expected_close_time": None,
                "price_change_percent": None,
                "current_price": current_price,
                "metrics": None,
                "history": history_points,
                "fundamental_analysis": None,
                "technical_recommendation": None
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading historical data: {str(e)}"
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
    current_user: Optional[User] = Depends(get_current_user_optional),
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


@router.get("/screener", response_model=List[MarketScreenerResponse])
def get_market_screener(db: Session = Depends(get_db)):
    """Returns all pre-calculated screener assets."""
    return db.query(MarketScreener).order_by(MarketScreener.symbol).all()


@router.get("/news/{symbol}", response_model=NewsSentimentResponse)
def get_news_sentiment(symbol: str):
    """Fetches articles and computes NLP sentiment analysis on the fly for the symbol."""
    symbol_upper = normalize_symbol(symbol)
    articles = fetch_symbol_news(symbol_upper)
    
    # Calculate overall sentiment score
    sentiment_score = 0.0
    if articles:
        sentiment_score = sum(a["score"] for a in articles) / len(articles)
        
    if sentiment_score >= 0.1:
        sentiment_class = "BULLISH"
    elif sentiment_score <= -0.1:
        sentiment_class = "BEARISH"
    else:
        sentiment_class = "NEUTRAL"
        
    return {
        "symbol": symbol_upper,
        "sentiment_score": sentiment_score,
        "sentiment_class": sentiment_class,
        "articles": articles
    }
