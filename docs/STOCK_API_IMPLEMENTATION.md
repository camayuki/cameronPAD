# Stock Tracking API Implementation Guide

**Date:** October 16, 2025  
**Based on:** Original `app/main.py` implementation

## Overview

The original CameronPAD stock tracker used real-time API calls to **Finnhub** (primary) and **Alpha Vantage** (fallback) to fetch stock prices, with automated alerts via SMS/Telegram/Discord, and linear regression predictions.

---

## API Providers

### 1. Finnhub API (Primary)
**URL:** https://finnhub.io  
**Free Tier:** 60 API calls/minute  
**Cost:** Free tier available  
**Endpoints Used:**

#### Quote Endpoint (Current Price)
```python
GET https://finnhub.io/api/v1/quote
Parameters:
  - symbol: "AAPL" (stock ticker)
  - token: YOUR_FINNHUB_TOKEN

Response:
{
  "c": 175.23,    # Current price
  "h": 176.45,    # High of day
  "l": 174.12     # Low of day
}
```

#### Candle Endpoint (Historical Data)
```python
GET https://finnhub.io/api/v1/stock/candle
Parameters:
  - symbol: "AAPL"
  - resolution: "D" (daily)
  - from: 1698336000 (unix timestamp)
  - to: 1701014400 (unix timestamp)
  - token: YOUR_FINNHUB_TOKEN

Response:
{
  "s": "ok",
  "c": [175.23, 176.45, 174.12, ...],  # Close prices
  "h": [176.50, 177.00, 175.50, ...],  # Highs
  "l": [174.00, 175.00, 173.50, ...]   # Lows
}
```

### 2. Alpha Vantage API (Fallback)
**URL:** https://www.alphavantage.co  
**Free Tier:** 5 API calls/minute, 500 calls/day  
**Cost:** Free tier available  
**Endpoints Used:**

#### Global Quote (Current Price)
```python
GET https://www.alphavantage.co/query
Parameters:
  - function: GLOBAL_QUOTE
  - symbol: AAPL
  - apikey: YOUR_ALPHA_VANTAGE_KEY

Response:
{
  "Global Quote": {
    "05. price": "175.23",
    "03. high": "176.45",
    "04. low": "174.12"
  }
}
```

#### Time Series Daily (Historical)
```python
GET https://www.alphavantage.co/query
Parameters:
  - function: TIME_SERIES_DAILY
  - symbol: AAPL
  - apikey: YOUR_ALPHA_VANTAGE_KEY

Response:
{
  "Time Series (Daily)": {
    "2025-10-16": {
      "4. close": "175.23",
      "2. high": "176.45",
      "3. low": "174.12"
    }
  }
}
```

---

## Original Implementation

### Environment Variables Required

```bash
# Stock APIs
FINNHUB_TOKEN=your_finnhub_token_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Polling intervals (seconds)
POLL_SECONDS=60              # Alert checking
SHOWCASE_REFRESH=300         # Showcase table update (5 min)
PREDICT_SECONDS=3600         # Predictions update (1 hour)

# Alert cooldown (minutes between repeat alerts)
COOLDOWN_MIN=0

# Showcase symbols (comma-separated)
SHOWCASE_SYMBOLS=AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,SPY

# Notification providers (optional)
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM=+1234567890
ALERT_PHONE=+1234567890

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

### Core Functions

#### 1. `fetch_quote(symbol: str)` - Get Current Price

```python
def fetch_quote(symbol: str):
    """Fetch current price, high, low from Finnhub (primary) or Alpha Vantage (fallback)"""
    
    # Try Finnhub first
    if FINNHUB:
        try:
            r = requests.get("https://finnhub.io/api/v1/quote",
                             params={"symbol": symbol, "token": FINNHUB},
                             timeout=10).json()
            p, h, l = r.get("c"), r.get("h"), r.get("l")
            if any(v is not None for v in (p, h, l)):
                return (float(p) if p is not None else None,
                        float(h) if h is not None else None,
                        float(l) if l is not None else None)
        except Exception:
            pass
    
    # Fallback to Alpha Vantage
    if ALPHA:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA}"
            q = alpha_get(url).json().get("Global Quote", {})
            p = q.get("05. price")
            h = q.get("03. high")
            l = q.get("04. low")
            return (float(p) if p else None,
                    float(h) if h else None,
                    float(l) if l else None)
        except Exception:
            pass
    
    return (None, None, None)
```

**Usage:**
```python
price, high, low = fetch_quote("AAPL")
# Returns: (175.23, 176.45, 174.12) or (None, None, None)
```

#### 2. `upsert_latest(conn, symbol, price, high, low)` - Cache Price

```python
def upsert_latest(conn, symbol: str, price, high, low):
    """Store/update latest price in database"""
    if price is None and high is None and low is None:
        return
    
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO latest_prices(symbol, price, high, low, ts)
      VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(symbol) DO UPDATE SET
        price=COALESCE(excluded.price, price),
        high=COALESCE(excluded.high, high),
        low=COALESCE(excluded.low, low),
        ts=CURRENT_TIMESTAMP
    """, (symbol, price, high, low))
    conn.commit()
```

**Database Table:**
```sql
CREATE TABLE IF NOT EXISTS latest_prices(
    symbol TEXT PRIMARY KEY,
    price REAL,
    high REAL,
    low REAL,
    ts TEXT
);
```

#### 3. `fetch_predict_15(symbol: str)` - Linear Regression Prediction

```python
def linear_regression_next(values):
    """Predict next value using linear regression"""
    n = len(values)
    if n < 5:
        return None
    
    xsum = n * (n + 1) / 2
    xxsum = n * (n + 1) * (2 * n + 1) / 6
    ysum = sum(values)
    xysum = sum((i + 1) * v for i, v in enumerate(values))
    
    denom = (n * xxsum - xsum * xsum)
    if denom == 0:
        return None
    
    slope = (n * xysum - xsum * ysum) / denom
    intercept = (ysum / n) - slope * (xsum / n)
    
    return intercept + slope * (n + 1)


def fetch_predict_15(symbol: str):
    """Fetch last 15 daily closes, predict next day using linear regression"""
    
    # Try Finnhub
    if FINNHUB:
        try:
            now = int(time.time())
            frm = now - 60 * 60 * 24 * 40  # 40 days back
            
            js = requests.get("https://finnhub.io/api/v1/stock/candle",
                              params={
                                  "symbol": symbol,
                                  "resolution": "D",
                                  "from": frm,
                                  "to": now,
                                  "token": FINNHUB
                              },
                              timeout=12).json()
            
            if js.get("s") == "ok":
                closes = (js.get("c") or [])[-15:]  # Last 15 closes
                if len(closes) >= 5:
                    pred = linear_regression_next(closes) or (sum(closes) / len(closes))
                    
                    # Store prediction
                    with db() as conn:
                        cur = conn.cursor()
                        cur.execute("""
                          INSERT INTO predictions(symbol, pred_next, src_days, ts)
                          VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                          ON CONFLICT(symbol) DO UPDATE SET
                            pred_next=excluded.pred_next,
                            src_days=excluded.src_days,
                            ts=CURRENT_TIMESTAMP
                        """, (symbol, float(pred), len(closes)))
                        conn.commit()
                    
                    return float(pred)
        except Exception:
            pass
    
    # Fallback to Alpha Vantage
    if ALPHA:
        try:
            js = alpha_get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA}").json()
            series = js.get("Time Series (Daily)", {}) or {}
            closes = []
            for d in sorted(series.keys()):
                v = series[d].get("4. close")
                if v:
                    closes.append(float(v))
            
            closes = closes[-15:]
            if len(closes) >= 5:
                pred = linear_regression_next(closes) or (sum(closes) / len(closes))
                
                # Store prediction
                with db() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                      INSERT INTO predictions(symbol, pred_next, src_days, ts)
                      VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                      ON CONFLICT(symbol) DO UPDATE SET
                        pred_next=excluded.pred_next,
                        src_days=excluded.src_days,
                        ts=CURRENT_TIMESTAMP
                    """, (symbol, float(pred), len(closes)))
                    conn.commit()
                
                return float(pred)
        except Exception:
            pass
    
    return None
```

**Database Table:**
```sql
CREATE TABLE IF NOT EXISTS predictions(
    symbol TEXT PRIMARY KEY,
    pred_next REAL,
    src_days INTEGER,
    ts TEXT
);
```

#### 4. `check_alerts()` - Background Alert Checking

```python
def check_alerts():
    """Check all enabled stock alerts, send notifications if triggered"""
    with db() as conn:
        cur = conn.cursor()
        
        # Get all enabled stock alerts
        cur.execute("SELECT id, symbol, target, direction FROM stocks WHERE enabled=1")
        
        for _id, sym, tgt, direction in cur.fetchall():
            # Fetch current price
            price, high, low = fetch_quote(sym)
            
            # Update cache
            upsert_latest(conn, sym, price, high, low)
            
            if price is None:
                continue
            
            # Check if alert triggered
            hit = (price >= tgt) if direction == "above" else (price <= tgt)
            
            if hit:
                # Check cooldown period
                cur.execute("SELECT ts FROM alerts WHERE symbol=? ORDER BY ts DESC LIMIT 1", (sym,))
                row = cur.fetchone()
                ok = True
                
                if row and COOLDOWN_MIN > 0:
                    last = datetime.fromisoformat(row[0])
                    ok = (datetime.utcnow() - last) >= timedelta(minutes=COOLDOWN_MIN)
                
                if ok:
                    # Log alert
                    cur.execute("INSERT INTO alerts(symbol, price, target, direction) VALUES(?, ?, ?, ?)",
                                (sym, price, tgt, direction))
                    conn.commit()
                    
                    # Send notifications
                    notify(f"[cameronpad] {sym} {direction} {tgt} (last {price:.2f})")
```

**Database Table:**
```sql
CREATE TABLE IF NOT EXISTS alerts(
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    price REAL,
    target REAL,
    direction TEXT,
    ts TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. Notification Functions

```python
def send_sms(msg: str):
    """Send SMS via Twilio"""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, ALERT_PHONE]):
        return
    
    try:
        requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            data={"From": TWILIO_FROM, "To": ALERT_PHONE, "Body": msg},
            auth=(TWILIO_SID, TWILIO_TOKEN),
            timeout=10
        )
    except Exception:
        pass


def send_telegram(msg: str):
    """Send message via Telegram Bot"""
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception:
        pass


def send_discord(msg: str):
    """Send message via Discord Webhook"""
    if not DISCORD_WEBHOOK_URL:
        return
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=10)
    except Exception:
        pass


def notify(msg: str):
    """Send notification to all configured channels"""
    send_sms(msg)
    send_telegram(msg)
    send_discord(msg)
```

#### 6. Background Schedulers

```python
from apscheduler.schedulers.background import BackgroundScheduler

def update_showcase():
    """Update showcase symbols (top stocks displayed)"""
    with db() as conn:
        for sym in SHOWCASE_SYMBOLS:
            p, h, l = fetch_quote(sym)
            upsert_latest(conn, sym, p, h, l)


def update_predictions():
    """Update predictions for all tracked symbols"""
    with db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM stocks WHERE enabled=1")
        syms = {r[0] for r in cur.fetchall()} | set(SHOWCASE_SYMBOLS)
    
    for s in syms:
        fetch_predict_15(s)


# Create scheduler
sched = BackgroundScheduler()

# Schedule jobs
sched.add_job(check_alerts, "interval", seconds=POLL_SECONDS, max_instances=1, coalesce=True)
sched.add_job(update_showcase, "interval", seconds=SHOWCASE_REFRESH, max_instances=1, coalesce=True)
sched.add_job(update_predictions, "interval", seconds=PREDICT_SECONDS, max_instances=1, coalesce=True)

# Start scheduler
sched.start()
```

**Schedule:**
- `check_alerts()` - Every 60 seconds
- `update_showcase()` - Every 300 seconds (5 minutes)
- `update_predictions()` - Every 3600 seconds (1 hour)

---

## Database Schema

```sql
-- Stock tracking
CREATE TABLE IF NOT EXISTS stocks(
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    target REAL,
    direction TEXT,  -- 'above' or 'below'
    enabled INTEGER DEFAULT 1
);

-- Latest cached prices
CREATE TABLE IF NOT EXISTS latest_prices(
    symbol TEXT PRIMARY KEY,
    price REAL,
    high REAL,
    low REAL,
    ts TEXT
);

-- Alert history
CREATE TABLE IF NOT EXISTS alerts(
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    price REAL,
    target REAL,
    direction TEXT,
    ts TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Price predictions
CREATE TABLE IF NOT EXISTS predictions(
    symbol TEXT PRIMARY KEY,
    pred_next REAL,
    src_days INTEGER,
    ts TEXT
);
```

---

## How to Get API Keys

### Finnhub (Recommended Primary)

1. Visit: https://finnhub.io
2. Click "Get free API key"
3. Sign up with email
4. Verify email
5. Copy API key from dashboard
6. Add to `.env`:
   ```bash
   FINNHUB_TOKEN=your_key_here
   ```

**Free Tier:**
- 60 API calls/minute
- Real-time stock prices
- Historical data
- No credit card required

### Alpha Vantage (Fallback)

1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email
3. Receive API key instantly
4. Add to `.env`:
   ```bash
   ALPHA_VANTAGE_KEY=your_key_here
   ```

**Free Tier:**
- 5 API calls/minute
- 500 API calls/day
- Real-time stock prices
- Historical data
- No credit card required

---

## Integration into New Plugin System

### File Structure

```
plugins/stocks/
├── config.yaml          # Plugin metadata
├── database.py          # Database initialization
├── services.py          # API integration (NEW)
├── plugin.py            # Routes and logic
└── templates/
    └── stocks.html      # UI
```

### Step 1: Create `services.py`

```python
"""
Stock API service for real-time prices and predictions
"""
import os
import time
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Get API keys from environment
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# Alpha Vantage rate limiting
ALPHA_MIN_INTERVAL = 13  # seconds between calls
_alpha_last_call = 0


def alpha_get(url: str):
    """Rate-limited Alpha Vantage requests"""
    global _alpha_last_call
    elapsed = time.time() - _alpha_last_call
    if elapsed < ALPHA_MIN_INTERVAL:
        time.sleep(ALPHA_MIN_INTERVAL - elapsed)
    _alpha_last_call = time.time()
    return requests.get(url, timeout=10)


def fetch_quote(symbol: str) -> tuple:
    """
    Fetch current price, high, low for symbol.
    Returns: (price, high, low) or (None, None, None)
    """
    # Try Finnhub first
    if FINNHUB_TOKEN:
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": FINNHUB_TOKEN},
                timeout=10
            ).json()
            
            p, h, l = r.get("c"), r.get("h"), r.get("l")
            if any(v is not None for v in (p, h, l)):
                logger.info(f"Fetched {symbol} from Finnhub: ${p}")
                return (
                    float(p) if p is not None else None,
                    float(h) if h is not None else None,
                    float(l) if l is not None else None
                )
        except Exception as e:
            logger.error(f"Finnhub error for {symbol}: {e}")
    
    # Fallback to Alpha Vantage
    if ALPHA_VANTAGE_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            q = alpha_get(url).json().get("Global Quote", {})
            
            p = q.get("05. price")
            h = q.get("03. high")
            l = q.get("04. low")
            
            if p:
                logger.info(f"Fetched {symbol} from Alpha Vantage: ${p}")
                return (
                    float(p) if p else None,
                    float(h) if h else None,
                    float(l) if l else None
                )
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
    
    logger.warning(f"Could not fetch price for {symbol}")
    return (None, None, None)


def linear_regression_next(values: list) -> float:
    """Predict next value using linear regression"""
    n = len(values)
    if n < 5:
        return None
    
    xsum = n * (n + 1) / 2
    xxsum = n * (n + 1) * (2 * n + 1) / 6
    ysum = sum(values)
    xysum = sum((i + 1) * v for i, v in enumerate(values))
    
    denom = (n * xxsum - xsum * xsum)
    if denom == 0:
        return None
    
    slope = (n * xysum - xsum * ysum) / denom
    intercept = (ysum / n) - slope * (xsum / n)
    
    return intercept + slope * (n + 1)


def fetch_predict_15(symbol: str) -> float:
    """
    Fetch last 15 daily closes, predict next day using linear regression.
    Returns: predicted_price or None
    """
    # Try Finnhub
    if FINNHUB_TOKEN:
        try:
            now = int(time.time())
            frm = now - 60 * 60 * 24 * 40  # 40 days back
            
            js = requests.get(
                "https://finnhub.io/api/v1/stock/candle",
                params={
                    "symbol": symbol,
                    "resolution": "D",
                    "from": frm,
                    "to": now,
                    "token": FINNHUB_TOKEN
                },
                timeout=12
            ).json()
            
            if js.get("s") == "ok":
                closes = (js.get("c") or [])[-15:]
                if len(closes) >= 5:
                    pred = linear_regression_next(closes)
                    if pred is None:
                        pred = sum(closes) / len(closes)
                    
                    logger.info(f"Predicted {symbol}: ${pred:.2f} (from {len(closes)} days)")
                    return float(pred)
        except Exception as e:
            logger.error(f"Finnhub prediction error for {symbol}: {e}")
    
    # Fallback to Alpha Vantage
    if ALPHA_VANTAGE_KEY:
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            js = alpha_get(url).json()
            series = js.get("Time Series (Daily)", {}) or {}
            
            closes = []
            for d in sorted(series.keys()):
                v = series[d].get("4. close")
                if v:
                    closes.append(float(v))
            
            closes = closes[-15:]
            if len(closes) >= 5:
                pred = linear_regression_next(closes)
                if pred is None:
                    pred = sum(closes) / len(closes)
                
                logger.info(f"Predicted {symbol}: ${pred:.2f} (from {len(closes)} days, Alpha)")
                return float(pred)
        except Exception as e:
            logger.error(f"Alpha Vantage prediction error for {symbol}: {e}")
    
    logger.warning(f"Could not generate prediction for {symbol}")
    return None


def upsert_latest_price(db_conn, symbol: str, price: float, high: float, low: float):
    """Store/update latest price in database"""
    if price is None and high is None and low is None:
        return
    
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO latest_prices(symbol, price, high, low, ts)
        VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(symbol) DO UPDATE SET
            price=COALESCE(excluded.price, price),
            high=COALESCE(excluded.high, high),
            low=COALESCE(excluded.low, low),
            ts=CURRENT_TIMESTAMP
    """, (symbol, price, high, low))
    db_conn.commit()
    logger.info(f"Updated cache for {symbol}: ${price}")


def upsert_prediction(db_conn, symbol: str, predicted_price: float, num_days: int):
    """Store/update prediction in database"""
    if predicted_price is None:
        return
    
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO predictions(symbol, pred_next, src_days, ts)
        VALUES(?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(symbol) DO UPDATE SET
            pred_next=excluded.pred_next,
            src_days=excluded.src_days,
            ts=CURRENT_TIMESTAMP
    """, (symbol, predicted_price, num_days))
    db_conn.commit()
    logger.info(f"Updated prediction for {symbol}: ${predicted_price:.2f}")
```

### Step 2: Update `plugin.py`

Add background tasks and API endpoints:

```python
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from .services import fetch_quote, fetch_predict_15, upsert_latest_price, upsert_prediction

class StocksPlugin(WebPlugin):
    def __init__(self):
        super().__init__()
        self.scheduler = None
    
    async def initialize(self):
        """Initialize plugin with background tasks"""
        await super().initialize()
        
        # Start background scheduler
        self.scheduler = BackgroundScheduler()
        
        # Check alerts every 60 seconds
        self.scheduler.add_job(
            self.check_alerts,
            "interval",
            seconds=60,
            max_instances=1,
            coalesce=True
        )
        
        # Update showcase every 5 minutes
        self.scheduler.add_job(
            self.update_showcase,
            "interval",
            seconds=300,
            max_instances=1,
            coalesce=True
        )
        
        # Update predictions every hour
        self.scheduler.add_job(
            self.update_predictions,
            "interval",
            seconds=3600,
            max_instances=1,
            coalesce=True
        )
        
        self.scheduler.start()
        logger.info("Stock background tasks started")
    
    def check_alerts(self):
        """Background task: check stock alerts"""
        conn = sqlite3.connect('data/cameronpad_dev.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, symbol, target, direction FROM stocks WHERE enabled=1")
        for stock_id, symbol, target, direction in cursor.fetchall():
            price, high, low = fetch_quote(symbol)
            upsert_latest_price(conn, symbol, price, high, low)
            
            if price is None:
                continue
            
            # Check if alert triggered
            triggered = (price >= target) if direction == "above" else (price <= target)
            
            if triggered:
                # Log alert
                cursor.execute(
                    "INSERT INTO alerts(symbol, price, target, direction) VALUES(?, ?, ?, ?)",
                    (symbol, price, target, direction)
                )
                conn.commit()
                logger.info(f"🚨 ALERT: {symbol} {direction} ${target} (current: ${price})")
        
        conn.close()
    
    def update_showcase(self):
        """Background task: update showcase stocks"""
        showcase = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
        conn = sqlite3.connect('data/cameronpad_dev.db')
        
        for symbol in showcase:
            price, high, low = fetch_quote(symbol)
            upsert_latest_price(conn, symbol, price, high, low)
        
        conn.close()
        logger.info(f"Updated {len(showcase)} showcase stocks")
    
    def update_predictions(self):
        """Background task: update price predictions"""
        conn = sqlite3.connect('data/cameronpad_dev.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT symbol FROM stocks WHERE enabled=1")
        symbols = [row[0] for row in cursor.fetchall()]
        
        for symbol in symbols:
            pred = fetch_predict_15(symbol)
            if pred:
                upsert_prediction(conn, symbol, pred, 15)
        
        conn.close()
        logger.info(f"Updated predictions for {len(symbols)} symbols")
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.scheduler:
            self.scheduler.shutdown()
        await super().shutdown()
```

---

## Testing

### 1. Test Quote Fetching

```python
# Test in Python console
from plugins.stocks.services import fetch_quote

price, high, low = fetch_quote("AAPL")
print(f"AAPL: ${price} (H: ${high}, L: ${low})")
```

### 2. Test Predictions

```python
from plugins.stocks.services import fetch_predict_15

predicted = fetch_predict_15("AAPL")
print(f"AAPL predicted next day: ${predicted}")
```

### 3. Monitor Logs

```bash
# Watch for API calls
tail -f logs/app.log | grep -i "stock\|finnhub\|alpha"
```

---

## Cost Analysis

### Free Tier Usage

**Finnhub (60 calls/min):**
- 8 showcase stocks × (1 quote/5min) = 96 calls/hour
- 10 tracked stocks × (1 quote/1min) = 600 calls/hour
- 10 tracked stocks × (1 candle/1hour) = 10 calls/hour
- **Total: ~706 calls/hour** ✅ Well within limits

**Alpha Vantage (5 calls/min, 500/day):**
- Only used as fallback
- Rate limited to 1 call per 13 seconds
- **Usage: Minimal** ✅

### Paid Tiers (Optional)

**Finnhub Pro ($50/mo):**
- Unlimited API calls
- Faster updates
- More data points

**Alpha Vantage Premium ($50/mo):**
- 1200 calls/minute
- Real-time data
- More endpoints

---

## Security Notes

1. **API Keys:** Store in `.env` file, never commit to Git
2. **Rate Limiting:** Respect API limits to avoid bans
3. **Error Handling:** Always catch exceptions to prevent crashes
4. **Timeouts:** Set reasonable timeouts (10-12 seconds)
5. **Caching:** Use database cache to reduce API calls

---

## Conclusion

The original stock tracker used a robust two-tier API system with Finnhub as primary and Alpha Vantage as fallback. It included:

✅ Real-time price fetching  
✅ Price predictions using linear regression  
✅ Automated alerts with cooldowns  
✅ Multi-channel notifications (SMS/Telegram/Discord)  
✅ Background scheduling for continuous updates  
✅ Database caching for performance  
✅ Comprehensive error handling  

All of this can be integrated into the new plugin system by creating a `services.py` module and adding background schedulers to `plugin.py`.

Next steps: Get API keys and integrate into new stocks plugin! 🚀
