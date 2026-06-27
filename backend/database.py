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
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        db.close()
