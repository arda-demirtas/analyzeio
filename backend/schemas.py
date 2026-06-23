from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime

# Authentication Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# Watchlist Schemas
class WatchlistAdd(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)

class WatchlistResponse(BaseModel):
    id: int
    symbol: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Machine Learning / Prediction Schemas
class IndicatorPoint(BaseModel):
    date: str
    open: float
    close: float
    volume: float
    high: Optional[float] = None
    low: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None

class PredictionMetrics(BaseModel):
    rmse: float
    mape: float
    directional_accuracy: float  # Percentage of days predicted direction matches actual direction
    training_status: str

class NewsArticle(BaseModel):
    title: str
    publisher: str
    link: str
    sentiment: str  # "Bullish", "Bearish", "Neutral"

class FundamentalAnalysisResult(BaseModel):
    sentiment_score: float
    sentiment_class: str  # "Bullish", "Bearish", "Neutral"
    recommendation: str
    articles: List[NewsArticle]

class PredictionResponse(BaseModel):
    symbol: str
    name: str
    last_date: str
    last_close: float
    predicted_close: float
    prediction_date: str
    expected_close_time: str
    price_change_percent: float
    current_price: Optional[float] = None
    metrics: PredictionMetrics
    history: List[IndicatorPoint]
    fundamental_analysis: Optional[FundamentalAnalysisResult] = None
