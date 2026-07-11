import os
import json
import datetime
from typing import Dict, Any, Tuple, Optional

from backend.config import MODEL_CACHE_DIR, AUTO_TRAINED_SYMBOLS, POPULAR_CRYPTOS
from backend.predictor import get_prediction
from backend.data_fetcher import fetch_market_data
from backend.sentiment import fetch_symbol_news

MOCK_STATE_FILE = os.path.join(MODEL_CACHE_DIR, "mock_trading_state.json")

def get_mock_trading_state() -> Dict[str, Any]:
    """Reads or initializes the mock trading state."""
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    if os.path.exists(MOCK_STATE_FILE):
        try:
            with open(MOCK_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Initialize default state
    default_state = {
        "balance": 2000.0,
        "position": None,
        "logs": [
            {
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "event": "Mock trading system initialized with $2,000.00 cash."
            }
        ]
    }
    save_mock_trading_state(default_state)
    return default_state

def save_mock_trading_state(state: Dict[str, Any]):
    """Saves the state to mock_trading_state.json."""
    with open(MOCK_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def log_mock_event(state: Dict[str, Any], event_text: str):
    """Appends a new event log to the state logs list."""
    state["logs"].append({
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "event": event_text
    })
    # Keep only the last 150 log entries to prevent file bloat
    if len(state["logs"]) > 150:
        state["logs"] = state["logs"][-150:]

def score_symbol_for_trading(symbol: str) -> float:
    """
    Computes a bullish preference score for the given symbol based on:
    1. Average predicted return across all 4 models (XGBoost, LSTM, Linear Regression, PatchTST)
       - Requires ALL 5 models (4 individual + 1 ensemble average) to be BULLISH (probability >= 50%).
    2. News Sentiment score
    3. Technical Indicators (RSI, MACD, EMA 50)
    """
    # 1. 4-Model predictions average expected return
    try:
        res = get_prediction(symbol, interval="1d", force_retrain=False)
        # Check if predictions are pending, locked, or unavailable
        if res.get("prediction_status") != "success":
            return -999.0
            
        last_close = res.get("last_close")
        xgb_close = res.get("xgb_predicted_close")
        lstm_close = res.get("lstm_predicted_close")
        lr_close = res.get("lr_predicted_close")
        patch_close = res.get("patchtst_predicted_close")
        
        if last_close is None or xgb_close is None or lstm_close is None or lr_close is None or patch_close is None:
            return -999.0
            
        # Consensus check: Require all 4 individual models to be BULLISH (probability >= 0.5)
        # (This automatically guarantees the Ensemble/Average model is also BULLISH)
        is_all_bullish = (xgb_close >= 0.5) and (lstm_close >= 0.5) and (lr_close >= 0.5) and (patch_close >= 0.5)
        if not is_all_bullish:
            return -999.0
            
        returns = []
        returns.append(xgb_close - 0.5)
        returns.append(lstm_close - 0.5)
        returns.append(lr_close - 0.5)
        returns.append(patch_close - 0.5)
            
        avg_expected_return = sum(returns) / len(returns)
    except Exception:
        return -999.0

    # 2. News Sentiment score
    sentiment_score = 0.0
    try:
        articles = fetch_symbol_news(symbol)
        if articles:
            sentiment_score = sum(a["score"] for a in articles) / len(articles)
    except Exception:
        pass

    # 3. Technical Indicators
    rsi = 50.0
    macd_hist = 0.0
    last_price = last_close
    ema_50 = last_close
    try:
        df, _, _, _ = fetch_market_data(symbol, interval="1d")
        if not df.empty:
            rsi = float(df["RSI"].iloc[-1]) if "RSI" in df.columns else 50.0
            macd_hist = float(df["MACD_Hist"].iloc[-1]) if "MACD_Hist" in df.columns else 0.0
            last_price = float(df["Close"].iloc[-1])
            ema_50 = float(df["EMA_50"].iloc[-1]) if "EMA_50" in df.columns else last_price
    except Exception:
        pass

    # Compute final score
    score = avg_expected_return
    # Factor news sentiment (up to +2% score)
    score += sentiment_score * 0.02
    # RSI Oversold bonus
    if rsi < 30:
        score += 0.015
    elif rsi > 70:
        score -= 0.015
    # MACD momentum bonus
    if macd_hist > 0:
        score += 0.005
    # Trend following bonus (above EMA 50)
    if last_price > ema_50:
        score += 0.005
        
    return score

def select_best_symbol_to_buy() -> Tuple[str, float]:
    """
    Finds the symbol with 5/5 bullish consensus (all 5 predictions >= 0.5)
    that has the highest average prediction score across all 5 models.
    Queries the database directly for performance and up-to-date values.
    """
    from backend.database import SessionLocal
    from backend.models import MarketScreener
    
    db = SessionLocal()
    try:
        entries = db.query(MarketScreener).all()
        best_symbol = ""
        best_avg = -999.0
        
        for entry in entries:
            # Check if all 5 model predictions are bullish (>= 0.5)
            if (entry.xgb_pred is not None and entry.xgb_pred >= 0.5 and
                entry.lstm_pred is not None and entry.lstm_pred >= 0.5 and
                entry.lr_pred is not None and entry.lr_pred >= 0.5 and
                entry.patchtst_pred is not None and entry.patchtst_pred >= 0.5 and
                entry.sr_pred is not None and entry.sr_pred >= 0.5):
                
                avg_score = (entry.xgb_pred + entry.lstm_pred + entry.lr_pred + entry.patchtst_pred + entry.sr_pred) / 5.0
                if avg_score > best_avg:
                    best_avg = avg_score
                    best_symbol = entry.symbol
                    
        return best_symbol, best_avg
    except Exception as e:
        print(f"[Mock Trading] Error selecting best symbol from DB: {e}")
        return "", -999.0
    finally:
        db.close()

def run_mock_trading_daily_buy(state=None) -> bool:
    """Tries to select and purchase the most bullish asset at the start of a daily candle."""
    # Enforce start time constraint: July 5th, 2026 at 03:00 UTC (06:00 TRT)
    start_time = datetime.datetime(2026, 7, 5, 3, 0, 0)
    if datetime.datetime.utcnow() < start_time:
        return False

    if state is None:
        state = get_mock_trading_state()
        
    # Check if we already have a position or a pending order
    if state.get("position") or state.get("pending_order"):
        return False
        
    balance = state.get("balance", 2000.0)
    if balance <= 1.0:  # No cash left to trade
        return False
        
    print("[Mock Trading] Executing daily selection and buy...")
    selected_symbol, score = select_best_symbol_to_buy()
    if not selected_symbol or score < -10.0:
        print("[Mock Trading] No valid symbol found for daily buy.")
        return False
        
    # Get the daily open price and yesterday's close price
    try:
        df, _, _, _ = fetch_market_data(selected_symbol, interval="1d")
        if df.empty:
            print(f"[Mock Trading] Data empty for {selected_symbol}")
            return False
        yesterday_close = float(df["Close"].iloc[-2])
        current_price = float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"[Mock Trading] Error loading prices for {selected_symbol}: {e}")
        return False
        
    now_utc = datetime.datetime.utcnow()
    
    # Entry Discount Rule: Buy immediately if current price is at or below yesterday's close price
    if current_price <= yesterday_close:
        qty = balance / current_price
        state["balance"] = 0.0
        state["position"] = {
            "symbol": selected_symbol,
            "entry_price": current_price,
            "qty": qty,
            "buy_time": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        state["pending_order"] = None
        
        event_str = f"OPENED position for {selected_symbol} immediately: Price (${current_price:,.2f}) is at/below yesterday's close (${yesterday_close:,.2f}). Purchased {qty:.6f} units."
        log_mock_event(state, event_str)
        save_mock_trading_state(state)
        print(f"[Mock Trading] {event_str}")
        return True
    else:
        # Otherwise, place a PENDING limit order at yesterday's close price
        qty = balance / yesterday_close
        state["pending_order"] = {
            "symbol": selected_symbol,
            "limit_price": yesterday_close,
            "qty": qty,
            "placed_time": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        event_str = f"Placed PENDING limit order for {selected_symbol}: Current price (${current_price:,.2f}) is above yesterday's close (${yesterday_close:,.2f}). Order placed at limit price ${yesterday_close:,.2f} for {qty:.6f} units."
        log_mock_event(state, event_str)
        save_mock_trading_state(state)
        print(f"[Mock Trading] {event_str}")
        return True

def check_mock_trading_rule():
    """
    Evaluates current active position or pending order against the rules:
    - 1.0% profit target (Take Profit)
    - 1.5% loss limit (Stop Loss)
    - End of day (23:50+ UTC or different calendar date) for position close or pending order cancel
    # - Daily 11:00 AM TRT (08:00 UTC) cycle reset and buy
    """
    # Enforce start time constraint: July 5th, 2026 at 03:00 UTC (06:00 TRT)
    start_time = datetime.datetime(2026, 7, 5, 3, 0, 0)
    now_utc = datetime.datetime.utcnow()
    if now_utc < start_time:
        return

    state = get_mock_trading_state()
    
    # 11:00 AM TRT (08:00 UTC) daily reset and buy (ensures all daily retry trainings have completed)
    today_str = now_utc.date().isoformat()
    if now_utc.hour == 8 and now_utc.minute >= 0 and state.get("last_buy_date") != today_str:
        print(f"[Mock Trading] Resetting cycle at {now_utc.strftime('%H:%M:%S UTC')}...")
        
        # Cancel any pending order from yesterday
        if state.get("pending_order"):
            pending = state["pending_order"]
            state["pending_order"] = None
            event_str = f"CANCELLED yesterday's pending order for {pending['symbol']}: Daily cycle reset reached without fill."
            log_mock_event(state, event_str)
            print(f"[Mock Trading] {event_str}")
            
        pos = state.get("position")
        if pos:
            symbol = pos["symbol"]
            qty = pos["qty"]
            entry_price = pos["entry_price"]
            try:
                df, _, _, current_price = fetch_market_data(symbol, interval="1d")
                if current_price is None and not df.empty:
                    current_price = float(df["Close"].iloc[-1])
                if current_price is None:
                    current_price = entry_price
            except Exception:
                current_price = entry_price
                
            new_balance = qty * current_price
            state["balance"] = float(round(new_balance, 2))
            state["position"] = None
            change_pct = (current_price - entry_price) / entry_price
            
            event_str = f"CLOSED position for {symbol} at daily cycle reset. Price: ${current_price:,.2f}. Gross Return: {change_pct*100:+.2f}%. New Cash Balance: ${state['balance']:,.2f}."
            log_mock_event(state, event_str)
            print(f"[Mock Trading] {event_str}")
            
        # Execute the new daily buy. Only set last_buy_date to today if a purchase or limit order was successfully placed.
        success = run_mock_trading_daily_buy(state)
        if success:
            state["last_buy_date"] = today_str
            save_mock_trading_state(state)
        else:
            # Save the close position logs anyway, but keep last_buy_date empty so it retries!
            save_mock_trading_state(state)
        return

    # Check if there is a pending limit order to execute
    pending = state.get("pending_order")
    if pending:
        symbol = pending["symbol"]
        limit_price = pending["limit_price"]
        qty = pending["qty"]
        placed_time_str = pending.get("placed_time")
        
        try:
            df, _, _, current_price = fetch_market_data(symbol, interval="1d")
            if current_price is None and not df.empty:
                current_price = float(df["Close"].iloc[-1])
        except Exception:
            current_price = None
            
        if current_price is not None:
            # If current price dipped to or below our limit price, execute the buy!
            if current_price <= limit_price:
                state["balance"] = 0.0
                state["position"] = {
                    "symbol": symbol,
                    "entry_price": limit_price,
                    "qty": qty,
                    "buy_time": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                state["pending_order"] = None
                
                event_str = f"PENDING limit order filled for {symbol}: Price dipped to ${current_price:,.2f} (Limit: ${limit_price:,.2f}). Entry price set to limit price. Position active."
                log_mock_event(state, event_str)
                save_mock_trading_state(state)
                print(f"[Mock Trading] {event_str}")
            else:
                # Cancel the pending order if 24 hours have passed or at the end of the day (23:50 UTC)
                should_cancel = False
                if now_utc.hour == 23 and now_utc.minute >= 50:
                    should_cancel = True
                elif placed_time_str:
                    try:
                        placed_dt = datetime.datetime.strptime(placed_time_str, "%Y-%m-%d %H:%M:%S UTC")
                        if now_utc.date() > placed_dt.date():
                            should_cancel = True
                    except Exception:
                        pass
                if should_cancel:
                    state["pending_order"] = None
                    event_str = f"CANCELLED pending order for {symbol}: Limit price (${limit_price:,.2f}) was not reached today (Current: ${current_price:,.2f})."
                    log_mock_event(state, event_str)
                    save_mock_trading_state(state)
                    print(f"[Mock Trading] {event_str}")

    pos = state.get("position")
    if not pos:
        return
        
    symbol = pos["symbol"]
    entry_price = pos["entry_price"]
    qty = pos["qty"]
    buy_time_str = pos.get("buy_time")
    
    # Fetch current price
    try:
        df, _, _, current_price = fetch_market_data(symbol, interval="1d")
        if current_price is None and not df.empty:
            current_price = float(df["Close"].iloc[-1])
        if current_price is None:
            return
    except Exception as e:
        print(f"[Mock Trading] Error fetching current price: {e}")
        return
        
    change_pct = (current_price - entry_price) / entry_price
    sell_reason = None
    
    # 1. Check Take Profit (+1.0%)
    if change_pct >= 0.010:
        sell_reason = f"Price hit profit target (+1.0% at ${current_price:,.2f})"
    # 2. Check Stop Loss (-1.5%)
    elif change_pct <= -0.015:
        sell_reason = f"Price hit stop loss (-1.5% at ${current_price:,.2f})"
    # 3. Check End of Day
    elif now_utc.hour == 23 and now_utc.minute >= 50:
        sell_reason = f"End of day reached (Close price: ${current_price:,.2f})"
    # 4. Roll-over fallback (different calendar date)
    elif buy_time_str:
        try:
            buy_dt = datetime.datetime.strptime(buy_time_str, "%Y-%m-%d %H:%M:%S UTC")
            if now_utc.date() > buy_dt.date():
                sell_reason = f"End of day rollover reached (Current price: ${current_price:,.2f})"
        except Exception:
            pass
            
    if sell_reason:
        # Execute Sell
        new_balance = qty * current_price
        state["balance"] = float(round(new_balance, 2))
        state["position"] = None
        
        event_str = f"CLOSED position for {symbol}: {sell_reason}. Sell Price: ${current_price:,.2f}. Gross Return: {change_pct*100:+.2f}%. New Cash Balance: ${state['balance']:,.2f}."
        log_mock_event(state, event_str)
        save_mock_trading_state(state)
        print(f"[Mock Trading] {event_str}")
