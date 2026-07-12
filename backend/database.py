from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

# Connect to SQLite/PostgreSQL conditionally
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    from sqlalchemy import text, inspect
    from backend.models import User, Watchlist, Comment, PredictionLog, AutoTrainSymbol, VerificationCode, MarketScreener, CommentReaction
    db = SessionLocal()
    try:
        # Inspect database schema in a database-agnostic way
        inspector = inspect(engine)
        if inspector.has_table("users"):
            columns = [col["name"] for col in inspector.get_columns("users")]
            if "profile_picture" not in columns:
                db.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255)"))
                db.commit()
                print("Successfully migrated database: added profile_picture to users table")
            if "is_premium" not in columns:
                db.execute(text("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE"))
                db.commit()
                print("Successfully migrated database: added is_premium to users table")
            
        # Ensure all tables are created
        Base.metadata.create_all(bind=engine)
        
        # Force all existing users to be premium for portfolio showcase
        db.execute(text("UPDATE users SET is_premium = TRUE"))
        db.commit()
        
        # Populate default and missing auto-train symbols
        from backend.models import AutoTrainSymbol, MarketScreener
        from backend.config import AUTO_TRAINED_SYMBOLS
        
        existing_symbols = {s.symbol for s in db.query(AutoTrainSymbol).all()}
        added_symbols = 0
        for sym in AUTO_TRAINED_SYMBOLS:
            if sym not in existing_symbols:
                db.add(AutoTrainSymbol(symbol=sym))
                added_symbols += 1
        if added_symbols > 0:
            db.commit()
            print(f"Populated database with {added_symbols} new auto-train symbols.")

        existing_screener = {s.symbol for s in db.query(MarketScreener).all()}
        added_screener = 0
        for sym in AUTO_TRAINED_SYMBOLS:
            if sym not in existing_screener:
                from backend.predictor import TICKER_NAMES
                name = TICKER_NAMES.get(sym, sym)
                db.add(MarketScreener(
                    symbol=sym,
                    name=name,
                    price=0.0,
                    predicted_change=0.0,
                    rsi=50.0,
                    macd_signal="NEUTRAL"
                ))
                added_screener += 1
        if added_screener > 0:
            db.commit()
            print(f"Populated database with {added_screener} new market screener entries.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        db.close()
