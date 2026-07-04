import datetime
from backend.data_fetcher import fetch_market_data

try:
    df, name, is_crypto, current_price = fetch_market_data("ASELS.IS", interval="1d")
    if not df.empty:
        print("Symbol: ASELS.IS")
        print("Name:", name)
        print("Total rows:", len(df))
        print("Last row index (date):", df.index[-1])
        print("Last Close price:", df["Close"].iloc[-1])
    else:
        print("ASELS.IS data is empty.")
except Exception as e:
    print("Error fetching ASELS.IS:", e)
