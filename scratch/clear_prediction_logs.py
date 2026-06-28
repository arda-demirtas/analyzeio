from backend.database import SessionLocal, engine
from backend.models import PredictionLog

db = SessionLocal()
try:
    db.query(PredictionLog).delete()
    db.commit()
    print("Database table prediction_logs cleared successfully!")
except Exception as e:
    print(f"Error clearing database: {e}")
finally:
    db.close()
