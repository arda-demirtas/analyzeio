import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String, nullable=True)
    is_premium = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlist_items")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    user = relationship("User")
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_user_reaction"),)

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reaction = Column(String, nullable=False)  # "like" or "dislike"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    comment = relationship("Comment", back_populates="reactions")
    user = relationship("User")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    interval = Column(String, nullable=False)
    prediction_date = Column(String, index=True, nullable=False)
    predicted_close = Column(Float, nullable=False)
    last_close = Column(Float, nullable=False)
    actual_close = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AutoTrainSymbol(Base):
    __tablename__ = "auto_train_symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False)  # "register" or "change_password"
    data = Column(String, nullable=True)     # JSON string with extra payload
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class MarketScreener(Base):
    __tablename__ = "market_screeners"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    predicted_change = Column(Float, nullable=True)  # Percent change
    rsi = Column(Float, nullable=True)
    macd_signal = Column(String, nullable=True)     # "BULLISH", "BEARISH", "NEUTRAL"
    xgb_pred = Column(Float, nullable=True)
    lstm_pred = Column(Float, nullable=True)
    lr_pred = Column(Float, nullable=True)
    patchtst_pred = Column(Float, nullable=True)
    sr_pred = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
