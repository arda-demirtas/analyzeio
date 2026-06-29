import os
import secrets

# JWT and Security Settings
# In production, this should be loaded from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database configuration
DATABASE_URL = "sqlite:///./analyzeio.db"

# Prediction settings
DEFAULT_SEQUENCE_LENGTH = 60
MODEL_CACHE_DIR = "./model_cache"

# Create directories if they do not exist
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

POPULAR_CRYPTOS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", 
    "SHIB-USD", "DOT-USD", "LINK-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "UNI-USD", "MATIC-USD", 
    "ICP-USD", "ETC-USD", "FIL-USD", "XLM-USD", "HBAR-USD", "ATOM-USD", "APT-USD", "VET-USD", 
    "RNDR-USD", "PEPE-USD", "OP-USD", "STX-USD", "GRT-USD", "LDO-USD", "INJ-USD", "THETA-USD", 
    "IMX-USD", "EGLD-USD", "FTM-USD", "ALGO-USD", "MKR-USD", "FLOW-USD", "MNT-USD", "AAVE-USD", 
    "SEI-USD", "AR-USD", "WIF-USD", "BONK-USD", "FLOKI-USD", "QNT-USD", "GALA-USD", "MANA-USD", 
    "AXS-USD", "SAND-USD", "JUP-USD", "PYTH-USD", "CHZ-USD", "DYDX-USD", "ENS-USD", "LRC-USD", 
    "ONE-USD", "CRO-USD", "TIA-USD", "MINA-USD"
]
