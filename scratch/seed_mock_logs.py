import datetime
from backend.database import SessionLocal, engine, Base
from backend.models import PredictionLog

# Ensure tables are created
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    # Clear existing logs to prevent duplicates
    db.query(PredictionLog).delete()
    
    # 1. BTC-USD Mock Logs (1d)
    btc_logs = [
        PredictionLog(
            symbol="BTC-USD",
            interval="1d",
            prediction_date="2026-06-25",
            predicted_close=59720.0,
            last_close=59300.0,
            actual_close=59910.0,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=4)
        ),
        PredictionLog(
            symbol="BTC-USD",
            interval="1d",
            prediction_date="2026-06-26",
            predicted_close=60100.0,
            last_close=59910.0,
            actual_close=60340.0,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=3)
        ),
        PredictionLog(
            symbol="BTC-USD",
            interval="1d",
            prediction_date="2026-06-27",
            predicted_close=60550.0,
            last_close=60340.0,
            actual_close=60120.0,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
        ),
        PredictionLog(
            symbol="BTC-USD",
            interval="1d",
            prediction_date="2026-06-28",
            predicted_close=59850.0,
            last_close=60120.0,
            actual_close=59980.0,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        ),
        PredictionLog(
            symbol="BTC-USD",
            interval="1d",
            prediction_date="2026-06-29",
            predicted_close=60250.0,
            last_close=59980.0,
            actual_close=None,
            created_at=datetime.datetime.utcnow()
        )
    ]
    
    # 2. TSLA Mock Logs (1d)
    tsla_logs = [
        PredictionLog(
            symbol="TSLA",
            interval="1d",
            prediction_date="2026-06-25",
            predicted_close=185.50,
            last_close=183.00,
            actual_close=186.20,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=4)
        ),
        PredictionLog(
            symbol="TSLA",
            interval="1d",
            prediction_date="2026-06-26",
            predicted_close=188.00,
            last_close=186.20,
            actual_close=187.90,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=3)
        ),
        PredictionLog(
            symbol="TSLA",
            interval="1d",
            prediction_date="2026-06-29",
            predicted_close=190.50,
            last_close=187.90,
            actual_close=None,
            created_at=datetime.datetime.utcnow()
        )
    ]
    
    db.add_all(btc_logs)
    db.add_all(tsla_logs)
    db.commit()
    print("Database successfully seeded with mock prediction logs!")
except Exception as e:
    print(f"Error seeding database: {e}")
finally:
    db.close()
