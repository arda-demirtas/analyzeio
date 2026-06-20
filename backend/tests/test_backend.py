import unittest
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, Watchlist
from backend.auth import get_password_hash, verify_password
from backend.predictor import calculate_rsi, calculate_macd

class TestAnalyzeioBackend(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database for testing database schemas."""
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        """Close database session and destroy tables."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_user_creation_and_password_hashing(self):
        """Verifies password hashing, database entry insertion, and deletion."""
        raw_password = "securePassword123"
        hashed = get_password_hash(raw_password)
        
        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("wrongPassword", hashed))
        
        # Test User Model
        user = User(
            username="testuser",
            email="testuser@example.com",
            hashed_password=hashed
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        db_user = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.email, "testuser@example.com")
        
        # Test Watchlist Relationship
        item = Watchlist(user_id=db_user.id, symbol="AAPL")
        self.db.add(item)
        self.db.commit()
        
        self.assertEqual(len(db_user.watchlist_items), 1)
        self.assertEqual(db_user.watchlist_items[0].symbol, "AAPL")
        
        # Test Account Close / Deletion cascading
        self.db.delete(db_user)
        self.db.commit()
        
        deleted_user = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNone(deleted_user)
        watchlist_count = self.db.query(Watchlist).filter(Watchlist.symbol == "AAPL").count()
        self.assertEqual(watchlist_count, 0) # Cascaded delete test

    def test_technical_indicators(self):
        """Verifies that technical indicator calculations return valid data bounds."""
        # Create dummy price series
        dates = pd.date_range(start="2026-01-01", periods=100)
        prices = pd.Series(
            [100.0 + np.sin(i/5)*10 + i/2 for i in range(100)],
            index=dates
        )
        
        # 1. RSI
        rsi = calculate_rsi(prices, period=14)
        self.assertEqual(len(rsi), 100)
        # RSI should range between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all())
        
        # 2. MACD
        macd, signal, hist = calculate_macd(prices, fast=12, slow=26, signal=9)
        self.assertEqual(len(macd), 100)
        self.assertEqual(len(signal), 100)
        self.assertEqual(len(hist), 100)
        
        # MACD Line should equal fast - slow EMA
        # Just verifying they output float series without errors
        self.assertTrue(isinstance(macd, pd.Series))
        self.assertTrue(isinstance(signal, pd.Series))
        self.assertTrue(isinstance(hist, pd.Series))

if __name__ == "__main__":
    unittest.main()
