from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL

# Connect to SQLite. check_same_thread is needed only for SQLite.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
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
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # Check if users table has profile_picture column
        result = db.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = [row[1] for row in result]
        if "profile_picture" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN profile_picture TEXT"))
            db.commit()
            print("Successfully migrated database: added profile_picture to users table")
        if "is_premium" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0"))
            db.commit()
            print("Successfully migrated database: added is_premium to users table")
            
        # Ensure all tables are created
        Base.metadata.create_all(bind=engine)
        
        # Populate default auto-train symbols if table is empty
        from backend.models import AutoTrainSymbol
        from backend.config import AUTO_TRAINED_SYMBOLS
        count = db.query(AutoTrainSymbol).count()
        if count == 0:
            for sym in AUTO_TRAINED_SYMBOLS:
                db.add(AutoTrainSymbol(symbol=sym))
            db.commit()
            print(f"Populated database with {len(AUTO_TRAINED_SYMBOLS)} default auto-train symbols.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        db.close()
