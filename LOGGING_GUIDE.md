# Stock Service Logging Guide

## Overview
Comprehensive Python logging has been added throughout the entire stock service data flow. All logs will appear in your **PowerShell terminal** where the uvicorn server is running.

## Logging Categories

### 🔵 [SERVICE] - Background Service Loop
Location: `plugins/stocks/plugin.py` - `update_loop()`

**What it shows:**
- Service start/stop events
- Monitoring cycle numbers with visual separators
- Timing information (poll intervals, showcase refresh intervals)
- Decision points (whether to update showcase or skip)

**Example Output:**
```
INFO:plugins.stocks.plugin:🔄 [SERVICE] ═══════════════════════════════════════════════════
INFO:plugins.stocks.plugin:🔄 [SERVICE] Starting monitoring cycle #1
INFO:plugins.stocks.plugin:🔄 [SERVICE] ═══════════════════════════════════════════════════
INFO:plugins.stocks.plugin:📊 [SERVICE] Time to update showcase! (counter=300s >= refresh=300s)
INFO:plugins.stocks.plugin:📊 [SERVICE] Starting showcase price update...
```

### 📊 [GUI UPDATE] - Service Layer Data Preparation
Location: `plugins/stocks/services.py` - `get_showcase_data()`

**What it shows:**
- When frontend requests data
- Database record counts (total prices available)
- Per-symbol data retrieval
- Data completeness summary

**Example Output:**
```
INFO:plugins.stocks.services:📊 [GUI UPDATE] get_showcase_data() called - preparing data for frontend
INFO:plugins.stocks.services:📊 [GUI UPDATE] Showcase symbols requested: AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, SPY
INFO:plugins.stocks.services:📊 [GUI UPDATE] Database has 8 total price records
INFO:plugins.stocks.services:📈 [GUI UPDATE] AAPL: Price=$247.45, High=$249.04, Low=$245.13, Time=2025-10-16 16:52:18
INFO:plugins.stocks.services:📊 [GUI UPDATE] Prepared 8 showcase records to send to frontend
INFO:plugins.stocks.services:📊 [GUI UPDATE] Data summary: 8 with prices, 0 without prices
```

### 💾 [DATABASE] - Data Storage Operations
Location: `plugins/stocks/services.py` - `_store_latest_price()`

**What it shows:**
- What data is being stored (symbol, price, high, low)
- Verification after INSERT/UPDATE
- Skip notifications when data is None

**Example Output:**
```
INFO:plugins.stocks.services:💾 [DATABASE] Storing AAPL → Price: $247.45, High: $249.04, Low: $245.13
INFO:plugins.stocks.services:✅ [DATABASE] AAPL stored successfully - Verified: Price=$247.45, High=$249.04, Low=$245.13
```

### 🌐 [ENDPOINT] - HTTP API Endpoint
Location: `plugins/stocks/plugin.py` - `/showcase` route

**What it shows:**
- When frontend calls the endpoint
- Database connection and query execution
- Query results (how many records returned)
- Per-symbol status (has data vs no data)
- Response summary before sending to frontend

**Example Output:**
```
INFO:plugins.stocks.plugin:🌐 [ENDPOINT] /showcase called by frontend - starting data retrieval
INFO:plugins.stocks.plugin:🔌 [ENDPOINT] Opening database connection...
INFO:plugins.stocks.plugin:📊 [ENDPOINT] Database query: 8 enabled stocks found
INFO:plugins.stocks.plugin:📊 [ENDPOINT] Database query: 8 stocks with prices found
INFO:plugins.stocks.plugin:🔍 [ENDPOINT] Executing JOIN query to fetch showcase data...
INFO:plugins.stocks.plugin:✅ [ENDPOINT] Query complete: 8 quotes retrieved
INFO:plugins.stocks.plugin:📈 [ENDPOINT] AAPL: ✅ HAS DATA | Price=$247.45, High=$249.04, Low=$245.13, Timestamp=2025-10-16 16:52:18
INFO:plugins.stocks.plugin:📤 [ENDPOINT] Sending response to frontend: status=success, 8 quotes
INFO:plugins.stocks.plugin:📤 [ENDPOINT] Response summary: 8 with prices, 0 without prices
```

### 📊🔵🟡 API Calls (Existing)
Location: `plugins/stocks/services.py` - `fetch_quote()` and `update_showcase_prices()`

**What it shows:**
- API call initiation (Finnhub primary, Alpha Vantage fallback)
- HTTP response status codes
- Data extraction (price, high, low)
- Success/failure for each symbol
- Overall summary statistics

**Example Output:**
```
INFO:plugins.stocks.services:📊 Fetching quote for AAPL...
INFO:plugins.stocks.services:🔵 Trying Finnhub API for AAPL...
INFO:plugins.stocks.services:🔵 Finnhub response status: 200
INFO:plugins.stocks.services:✅ Finnhub success for AAPL: price=$247.45, high=$249.04, low=$245.13
INFO:plugins.stocks.services:📊 Updating showcase prices for 8 symbols: AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, SPY
INFO:plugins.stocks.services:✅ Showcase update complete: 8 successful, 0 failed
```

## Complete Data Flow Trace

### When Service Starts and Updates Showcase:

1. **Service Loop Triggers Update**
   ```
   🔄 [SERVICE] Starting monitoring cycle #1
   📊 [SERVICE] Time to update showcase!
   📊 [SERVICE] Starting showcase price update...
   ```

2. **Service Fetches from APIs**
   ```
   📊 Updating showcase prices for 8 symbols: AAPL, MSFT, ...
   📊 Fetching quote for AAPL...
   🔵 Trying Finnhub API for AAPL...
   ✅ Finnhub success: price=$247.45, high=$249.04, low=$245.13
   ```

3. **Service Stores in Database**
   ```
   💾 [DATABASE] Storing AAPL → Price: $247.45, High: $249.04, Low: $245.13
   ✅ [DATABASE] AAPL stored successfully - Verified: Price=$247.45...
   ```

4. **Service Completes Update**
   ```
   ✅ Showcase update complete: 8 successful, 0 failed
   ✅ [SERVICE] Showcase prices update complete!
   ```

### When Frontend Requests Data:

1. **Frontend Calls Endpoint**
   ```
   🌐 [ENDPOINT] /showcase called by frontend - starting data retrieval
   ```

2. **Endpoint Queries Database**
   ```
   🔌 [ENDPOINT] Opening database connection...
   📊 [ENDPOINT] Database query: 8 enabled stocks found
   📊 [ENDPOINT] Database query: 8 stocks with prices found
   ```

3. **Endpoint Retrieves and Logs Data**
   ```
   🔍 [ENDPOINT] Executing JOIN query to fetch showcase data...
   ✅ [ENDPOINT] Query complete: 8 quotes retrieved
   📈 [ENDPOINT] AAPL: ✅ HAS DATA | Price=$247.45, High=$249.04, Low=$245.13
   ```

4. **Endpoint Sends Response**
   ```
   📤 [ENDPOINT] Sending response to frontend: status=success, 8 quotes
   📤 [ENDPOINT] Response summary: 8 with prices, 0 without prices
   ```

## How to Monitor Your Application

### 1. Watch the Terminal
Your PowerShell terminal running uvicorn will show ALL these logs in real-time.

### 2. Start the Stock Service
1. Go to http://127.0.0.1:8000/api/v1/plugins/stocks/
2. Click "Start Service" button
3. Watch the terminal - you'll see:
   - Initial showcase update (immediate)
   - Monitoring cycle logs every 60 seconds
   - Showcase updates every 5 minutes (300 seconds)

### 3. Look for Key Indicators

**✅ Everything Working:**
```
✅ [DATABASE] AAPL stored successfully
✅ [ENDPOINT] Query complete: 8 quotes retrieved
✅ HAS DATA | Price=$247.45
📤 Response summary: 8 with prices, 0 without prices
```

**⚠️ Service Not Running (Expected before start):**
```
⚠️ [ENDPOINT] WARNING: latest_prices table is EMPTY!
❌ NO DATA | Price=--
📤 Response summary: 0 with prices, 8 without prices
```

**❌ API Issues:**
```
❌ Finnhub HTTP 401 for AAPL
🟡 Falling back to Alpha Vantage
❌❌ Failed to fetch quote for AAPL from all sources
```

## Environment Variables

Control logging behavior through `.env`:

- `POLL_SECONDS=60` - How often to check for updates (default: 60)
- `SHOWCASE_REFRESH=300` - How often to update showcase (default: 300 = 5 minutes)

**Tip:** For testing, set `SHOWCASE_REFRESH=60` to update every minute.

## Troubleshooting with Logs

### Problem: Prices showing as "--"

**Look for:**
```
⚠️ [ENDPOINT] WARNING: latest_prices table is EMPTY!
```
**Solution:** Start the stock service

---

### Problem: Service running but no updates

**Look for:**
```
⏭️ [SERVICE] Skipping showcase update (counter=60s < refresh=300s)
```
**Solution:** Wait for the showcase refresh interval, or reduce `SHOWCASE_REFRESH` in .env

---

### Problem: Some stocks have data, others don't

**Look for:**
```
❌ Failed to fetch quote for TSLA from all sources
```
**Solution:** API might be throttling, check rate limits

---

### Problem: Data in database but not showing on page

**Look for endpoint logs:**
```
📈 [ENDPOINT] AAPL: ✅ HAS DATA | Price=$247.45
```
**Solution:** If endpoint shows data, check browser console (JavaScript logs)

## Log Levels

- **INFO** - Normal operations, data flow tracking
- **DEBUG** - Detailed step-by-step operations (may be hidden by default)
- **WARNING** - Non-critical issues (empty data, skipped operations)
- **ERROR** - Critical failures (API errors, database errors)

## Additional Frontend Logging

The frontend (JavaScript) also has console logging. Press **F12** in your browser and check the Console tab:

```javascript
🔄 [SHOWCASE] Starting refresh...
📊 [SHOWCASE] Received data: [8 quotes]
📈 [SHOWCASE] Processing AAPL: {price: 247.45, high: 249.04, low: 245.13}
💲 [SHOWCASE] AAPL price: -- → $247.45
✅ [SHOWCASE] Update complete: 8 updated, 0 skipped
```

Together, the **Python logs in PowerShell** and **JavaScript logs in Browser Console** give you complete visibility into the entire data flow!

## Performance Monitoring

Watch these logs to identify bottlenecks:

- **API Response Times:** Check time between "Trying Finnhub" and "Finnhub success"
- **Database Operations:** Look for delays between "Storing" and "stored successfully"
- **Cycle Duration:** Time between "Starting cycle" and "cycle complete"

## Summary

With this comprehensive logging, you can now:
- ✅ Track every step of data flow from API → Database → Frontend
- ✅ Identify exactly where issues occur
- ✅ Verify data is being stored and retrieved correctly
- ✅ Monitor service health in real-time
- ✅ Debug issues quickly with detailed context

All logs appear in your **PowerShell terminal** where you run the uvicorn server!
