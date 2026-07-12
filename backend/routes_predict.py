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
    if sym == "UNI-USD":
        sym = "UNI7083-USD"
    return sym

@router.get("/predict", response_model=PredictionResponse)
def predict_asset(symbol: str, interval: str = "1d", lang: str = "en", model_type: str = "analyzeio", force_retrain: bool = False, current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    Triggers historical data loading, computes technical indicators,
    and runs XGBoost (default) or LSTM model inference to predict the close price for the next candle of the selected interval.
    """
    symbol_upper = normalize_symbol(symbol)
    if interval not in ["15m", "1h", "4h", "1d"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported interval. Allowed: 15m, 1h, 4h, 1d"
        )
    if model_type not in ["xgboost", "lstm", "linear_regression", "patchtst", "support_resistance", "analyzeio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported model_type. Allowed: xgboost, lstm, linear_regression, patchtst, support_resistance, analyzeio"
        )
    is_btc = symbol_upper == "BTC-USD"
    is_premium = True
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
        prediction_result = get_prediction(symbol_upper, interval=interval, lang=lang, model_type=model_type, force_retrain=force_retrain)
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


@router.get("/market-info/{symbol}")
def get_market_info(symbol: str):
    """
    Returns extra market metadata using Yahoo Finance v8 chart API directly
    (same endpoint used for price history - not rate-limited on VPS).
    Fields: 52-week range, daily volume, exchange name, currency, long name.
    """
    import requests as req_lib
    symbol_upper = normalize_symbol(symbol)

    _EMPTY = {
        "symbol": symbol_upper,
        "market_cap": None,
        "average_volume": None,
        "regular_market_volume": None,
        "fifty_two_week_high": None,
        "fifty_two_week_low": None,
        "trailing_pe": None,
        "dividend_yield": None,
        "sector": None,
        "industry": None,
        "circulating_supply": None,
        "currency": "USD",
        "exchange_name": None,
        "long_name": None,
        "instrument_type": None,
        "day_high": None,
        "day_low": None,
    }

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        # Fetch 60 days of daily data – meta block contains 52-week range & volume
        url = (
            f"https://query2.finance.yahoo.com/v8/finance/chart/"
            f"{symbol_upper}?range=60d&interval=1d"
        )
        r = req_lib.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            return _EMPTY

        data = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return _EMPTY

        meta = result[0].get("meta", {})
        quote = result[0].get("indicators", {}).get("quote", [{}])[0]

        # Compute 20-day average volume from actual bars
        volumes = [v for v in (quote.get("volume") or []) if v is not None]
        last_20_vols = volumes[-20:] if len(volumes) >= 20 else volumes
        avg_volume = int(sum(last_20_vols) / len(last_20_vols)) if last_20_vols else None

        instrument_type = meta.get("instrumentType", "")
        is_crypto = instrument_type == "CRYPTOCURRENCY" or symbol_upper.endswith("-USD")

        # Rough market cap for crypto: price × circulating supply (not available here, skip)
        # For equities it's not in v8; leave as None (not rate-limited fields show correctly)

        return {
            "symbol": symbol_upper,
            "market_cap": None,          # Not available in v8 without .info
            "average_volume": avg_volume,
            "regular_market_volume": meta.get("regularMarketVolume"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            "trailing_pe": None,         # Not in v8 chart
            "dividend_yield": None,      # Not in v8 chart
            "sector": None,
            "industry": None,
            "circulating_supply": None,
            "currency": meta.get("currency", "USD"),
            "exchange_name": meta.get("fullExchangeName"),
            "long_name": meta.get("longName") or meta.get("shortName"),
            "instrument_type": instrument_type,
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
        }
    except Exception:
        return _EMPTY


@router.get("/search")
def search_assets(q: str):
    """
    Proxies a search query to Yahoo Finance search endpoint
    and returns mapped symbol suggestions.
    """
    import requests as req_lib
    if not q or not q.strip():
        return []

    # Clean and preprocess query (e.g. bist100 -> bist 100, bist30 -> bist 30)
    q_query = q.strip().lower()
    import re
    q_query = re.sub(r"bist(\d+)", r"bist \1", q_query)

    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": q_query, "quotesCount": 10}
    headers = {

        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        r = req_lib.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
        quotes = data.get("quotes", [])

        results = []
        for quote in quotes:
            symbol = quote.get("symbol")
            if not symbol:
                continue

            # Map type
            qtype = quote.get("quoteType", "")
            category = "Stock"
            if qtype:
                qtype_upper = qtype.upper()
                if qtype_upper == "CRYPTOCURRENCY":
                    category = "Crypto"
                elif qtype_upper == "INDEX":
                    category = "Index"
                elif qtype_upper == "ETF":
                    category = "ETF"
                elif qtype_upper == "EQUITY":
                    if symbol.endswith(".IS"):
                        category = "BIST"
                    else:
                        category = "Stock"
                elif qtype_upper == "FUTURE":
                    if symbol in ["GC=F", "SI=F"]:
                        category = "Commodity"
                    else:
                        category = "Future"
                else:
                    category = qtype.replace("_", " ").title()

            # Name
            name = quote.get("longname") or quote.get("shortname") or symbol

            results.append({
                "symbol": symbol,
                "name": name,
                "category": category
            })
        return results
    except Exception:
        return []

