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
