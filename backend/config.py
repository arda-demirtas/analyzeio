import os
import secrets

# JWT and Security Settings
# In production, this should be loaded from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "7b9e7d9c8b7f8e7d6c5b4a3b2a1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analyzeio.db")

# Prediction settings
DEFAULT_SEQUENCE_LENGTH = 60
MODEL_CACHE_DIR = "./model_cache"

# Create directories if they do not exist
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

POPULAR_CRYPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", 
    "SHIB-USD", "DOT-USD", "LINK-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "UNI7083-USD", "MATIC-USD", 
    "ICP-USD", "ETC-USD", "FIL-USD", "XLM-USD", "HBAR-USD", "ATOM-USD", "APT-USD", "VET-USD", 
    "RNDR-USD", "PEPE-USD", "OP-USD", "STX-USD", "GRT-USD", "LDO-USD", "INJ-USD", "THETA-USD", 
    "IMX-USD", "EGLD-USD", "FTM-USD", "ALGO-USD", "MKR-USD", "FLOW-USD", "MNT-USD", "AAVE-USD", 
    "SEI-USD", "AR-USD", "WIF-USD", "BONK-USD", "FLOKI-USD", "QNT-USD", "GALA-USD", "MANA-USD", 
    "AXS-USD", "SAND-USD", "JUP-USD", "PYTH-USD", "CHZ-USD", "DYDX-USD", "ENS-USD", "LRC-USD", 
    "ONE-USD", "CRO-USD", "TIA-USD", "MINA-USD"
]

POPULAR_COMMODITIES = ["GC=F", "SI=F"]

POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY", "AVGO",
    "JPM", "V", "UNH", "TSM", "WMT", "XOM", "MA", "PG", "JNJ", "HD",
    "ASML", "ORCL", "COST", "MRK", "CVX", "BAC", "ABBV", "AMD", "NFLX", "PEP",
    "KO", "TMO", "WFC", "DIS", "ADBE", "AZN", "CSCO", "QCOM", "NVO", "ACN",
    "SAP", "GE", "CAT", "AMGN", "TXN", "INTC", "IBM", "AXP", "MS", "PFE",
    "GS", "HON", "NKE", "SBUX", "UBER", "INTU", "ISRG", "LRCX", "SYK", "BA"
]

AUTO_TRAINED_SYMBOLS = POPULAR_CRYPTOS + POPULAR_COMMODITIES + POPULAR_STOCKS
