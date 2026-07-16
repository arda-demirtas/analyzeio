import os
# Limit CPU threads to 1 ONLY on Linux (VPS) to prevent lockups, allow full multi-threading on Windows (Local)
if os.name != "nt":
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"

try:
    import tensorflow as tf
    if os.name != "nt":
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
except ImportError:
    pass

import secrets

# Load environment variables from .env file in the root project folder without external dependencies
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# JWT and Security Settings
# In production, this should be loaded from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "7b9e7d9c8b7f8e7d6c5b4a3b2a1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), 'analyzeio.db'))}")

# Prediction settings
DEFAULT_SEQUENCE_LENGTH = 60
MODEL_CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "model_cache"))

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
    "GS", "HON", "NKE", "SBUX", "UBER", "INTU", "ISRG", "LRCX", "SYK", "BA",
    "THYAO.IS", "EREGL.IS", "GARAN.IS", "KCHOL.IS", "AKBNK.IS", "ASELS.IS", 
    "TUPRS.IS", "SISE.IS", "TCELL.IS", "BIMAS.IS",
    # Asian Stocks (Tokyo)
    "7203.T", "6758.T", "9984.T", "8306.T", "8035.T", "7974.T", "9432.T", "6861.T", 
    "6098.T", "4063.T", "8316.T", "8411.T", "9983.T", "8058.T", "8001.T",
    # Asian Stocks (Hong Kong)
    "0700.HK", "0941.HK", "0005.HK", "0939.HK", "1299.HK", "1398.HK", "0883.HK", "2318.HK", 
    "9988.HK", "3988.HK", "2388.HK", "0001.HK", "0016.HK", "0011.HK", "3690.HK"
]

AUTO_TRAINED_SYMBOLS = POPULAR_CRYPTOS + POPULAR_COMMODITIES + POPULAR_STOCKS

FEATURES = [
    "Return_Lag1", "Return_Lag3", "Return_Lag5",
    "RSI", "MACD_Hist", "EMA_Diff", "BB_Position", "ATR_Percent",
    "SPY_Return_1d", "SPY_Return_5d", "VIX_Close"
]


TICKER_NAMES = {
    "BTC-USD": "Bitcoin USD",
    "ETH-USD": "Ethereum USD",
    "AAPL": "Apple Inc.",
    "TSLA": "Tesla Inc.",
    "GC=F": "Gold Futures",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "BTC-USDT": "Bitcoin USD",
    "ETH-USDT": "Ethereum USD",
    "UNI7083-USD": "Uniswap USD",
    "THYAO.IS": "Türk Hava Yolları",
    "EREGL.IS": "Ereğli Demir Çelik",
    "GARAN.IS": "Garanti BBVA",
    "KCHOL.IS": "Koç Holding",
    "AKBNK.IS": "Akbank",
    "ASELS.IS": "Aselsan",
    "TUPRS.IS": "Tüpraş",
    "SISE.IS": "Şişecam",
    "TCELL.IS": "Turkcell",
    "BIMAS.IS": "BİM Birleşik Mağazalar",
    # Tokyo Stocks
    "7203.T": "Toyota Motor",
    "6758.T": "Sony Group",
    "9984.T": "SoftBank Group",
    "8306.T": "Mitsubishi UFJ",
    "8035.T": "Tokyo Electron",
    "7974.T": "Nintendo",
    "9432.T": "NTT",
    "6861.T": "Keyence",
    "6098.T": "Recruit Holdings",
    "4063.T": "Shin-Etsu Chemical",
    "8316.T": "Sumitomo Mitsui",
    "8411.T": "Mizuho Financial",
    "9983.T": "Fast Retailing",
    "8058.T": "Mitsubishi Corp",
    "8001.T": "Itochu Corp",
    # Hong Kong Stocks
    "0700.HK": "Tencent Holdings",
    "0941.HK": "China Mobile",
    "0005.HK": "HSBC Holdings",
    "0939.HK": "China Construction Bank",
    "1299.HK": "AIA Group",
    "1398.HK": "ICBC",
    "0883.HK": "CNOOC",
    "2318.HK": "Ping An Insurance",
    "9988.HK": "Alibaba Group",
    "3988.HK": "Bank of China",
    "2388.HK": "BOC Hong Kong",
    "0001.HK": "CK Hutchison",
    "0016.HK": "Sun Hung Kai",
    "0011.HK": "Hang Seng Bank",
    "3690.HK": "Meituan"
}
