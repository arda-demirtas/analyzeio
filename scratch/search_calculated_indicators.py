import sys
sys.path.append("c:/Users/h1z1a/Desktop/Analyzeio")
from backend.data_fetcher import fetch_market_data

df, name, is_crypto, price = fetch_market_data("BTC-USD", "1d")
print("Columns in market data DataFrame:")
for col in sorted(df.columns):
    print(f"  {col}")
