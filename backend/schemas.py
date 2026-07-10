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

class VerificationConfirm(BaseModel):
    email: EmailStr
    code: str

class CodeConfirm(BaseModel):
    code: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    profile_picture: Optional[str] = None
    is_premium: bool = False
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
    lr_predicted_close: Optional[float] = None
    atr: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    obv: Optional[float] = None
    cci: Optional[float] = None
    williams_r: Optional[float] = None

class PredictionMetrics(BaseModel):
    rmse: Optional[float] = None
    mape: Optional[float] = None
    logloss: Optional[float] = None
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

class TechnicalRecommendation(BaseModel):
    signal: str  # "STRONG_BUY", "STRONG_SELL", "HOLD"
    text: str

class PredictionResponse(BaseModel):
    symbol: str
    name: str
    last_date: str
    last_close: float
    predicted_close: Optional[float] = None
    prediction_date: Optional[str] = None
    expected_close_time: Optional[str] = None
    candle_open_time: Optional[str] = None
    candle_close_time: Optional[str] = None
    price_change_percent: Optional[float] = None
    current_price: Optional[float] = None
    metrics: Optional[PredictionMetrics] = None
    history: List[IndicatorPoint]
    prediction_status: Optional[str] = None
    prediction_error: Optional[str] = None
    model_type: Optional[str] = None
    xgb_predicted_close: Optional[float] = None
    lstm_predicted_close: Optional[float] = None
    lr_predicted_close: Optional[float] = None
    patchtst_predicted_close: Optional[float] = None
    sr_predicted_close: Optional[float] = None
    analyzeio_predicted_close: Optional[float] = None
    xgb_metrics: Optional[PredictionMetrics] = None
    lstm_metrics: Optional[PredictionMetrics] = None
    lr_metrics: Optional[PredictionMetrics] = None
    patchtst_metrics: Optional[PredictionMetrics] = None
    sr_metrics: Optional[PredictionMetrics] = None
    analyzeio_metrics: Optional[PredictionMetrics] = None
    fundamental_analysis: Optional[FundamentalAnalysisResult] = None
    technical_recommendation: Optional[TechnicalRecommendation] = None






# Profile & Comments schemas
class ProfilePictureUpdate(BaseModel):
    profile_picture: str  # Base64 string

class CommentCreate(BaseModel):
    symbol: str
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[int] = None

class CommentUser(BaseModel):
    id: int
    username: str
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True

class CommentResponse(BaseModel):
    id: int
    symbol: str
    content: str
    created_at: datetime.datetime
    parent_id: Optional[int] = None
    user: CommentUser
    likes: int = 0
    dislikes: int = 0
    user_reaction: Optional[str] = None  # "like", "dislike", or None

    class Config:
        from_attributes = True

class CommentReactRequest(BaseModel):
    reaction: str  # "like" or "dislike"

class PredictionLogResponse(BaseModel):
    id: int
    symbol: str
    interval: str
    prediction_date: str
    predicted_close: float
    last_close: float
    actual_close: Optional[float] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class AutoTrainSymbolResponse(BaseModel):
    id: int
    symbol: str
    created_at: datetime.datetime
    last_trained_at: Optional[str] = None
    is_trained: Optional[bool] = False

    class Config:
        from_attributes = True


class AutoTrainSymbolAdd(BaseModel):
    symbol: str


class MarketScreenerResponse(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    price: float
    predicted_change: Optional[float] = None
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class NewsArticleResponse(BaseModel):
    title: str
    publisher: str
    link: str
    time: int
    score: float
    rating: str


class NewsSentimentResponse(BaseModel):
    symbol: str
    sentiment_score: float
    sentiment_class: str
    articles: List[NewsArticleResponse]

