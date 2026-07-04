from backend.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()
try:
    dialect_name = engine.dialect.name
    print(f"Dialect: {dialect_name}")

    # List all tables in current database
    if dialect_name == "sqlite":
        res_tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    else:
        res_tables = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
    
    print("Tables in database:")
    for t_name in res_tables:
        print(f"  {t_name[0]}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
