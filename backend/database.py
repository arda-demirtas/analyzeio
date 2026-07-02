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
        
        # Populate default auto-train symbols if table is empty
        from backend.models import AutoTrainSymbol, MarketScreener
        from backend.config import AUTO_TRAINED_SYMBOLS
        count = db.query(AutoTrainSymbol).count()
        if count == 0:
            for sym in AUTO_TRAINED_SYMBOLS:
                db.add(AutoTrainSymbol(symbol=sym))
            db.commit()
            print(f"Populated database with {len(AUTO_TRAINED_SYMBOLS)} default auto-train symbols.")

        screener_count = db.query(MarketScreener).count()
        if screener_count == 0:
            from backend.predictor import TICKER_NAMES
            for sym in AUTO_TRAINED_SYMBOLS:
                name = TICKER_NAMES.get(sym, sym)
                db.add(MarketScreener(
                    symbol=sym,
                    name=name,
                    price=0.0,
                    predicted_change=0.0,
                    rsi=50.0,
                    macd_signal="NEUTRAL"
                ))
            db.commit()
            print(f"Populated database with {len(AUTO_TRAINED_SYMBOLS)} default market screener entries.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        db.close()
