# 🔍 Enhanced Debug Logging - Quick Reference

## What You'll See in Your PowerShell Terminal

### ✅ Current State (Service NOT Started):
```powershell
INFO:plugins.stocks.plugin:🌐 [ENDPOINT] /showcase called by frontend - starting data retrieval
INFO:plugins.stocks.plugin:🔌 [ENDPOINT] Opening database connection...
INFO:plugins.stocks.plugin:📊 [ENDPOINT] Database query: 8 enabled stocks found
INFO:plugins.stocks.plugin:📊 [ENDPOINT] Database query: 0 stocks with prices found
WARNING:plugins.stocks.plugin:⚠️ [ENDPOINT] WARNING: latest_prices table is EMPTY! Service may not be running.
INFO:plugins.stocks.plugin:📈 [ENDPOINT] AAPL: ❌ NO DATA | Price=$None, High=$None, Low=$None, Timestamp=None
INFO:plugins.stocks.plugin:📤 [ENDPOINT] Response summary: 0 with prices, 8 without prices
```

### 🎯 After Starting Service (What to Look For):
```powershell
INFO:plugins.stocks.plugin:🔄 [SERVICE] ═══════════════════════════════════════════════════
INFO:plugins.stocks.plugin:🔄 [SERVICE] Starting monitoring cycle #1
INFO:plugins.stocks.plugin:📊 [SERVICE] Time to update showcase! (counter=300s >= refresh=300s)
INFO:plugins.stocks.services:📊 Updating showcase prices for 8 symbols: AAPL, MSFT, GOOGL...
INFO:plugins.stocks.services:📊 Fetching quote for AAPL...
INFO:plugins.stocks.services:🔵 Trying Finnhub API for AAPL...
INFO:plugins.stocks.services:✅ Finnhub success for AAPL: price=$247.45, high=$249.04, low=$245.13
INFO:plugins.stocks.services:💾 [DATABASE] Storing AAPL → Price: $247.45, High: $249.04, Low: $245.13
INFO:plugins.stocks.services:✅ [DATABASE] AAPL stored successfully - Verified: Price=$247.45, High=$249.04, Low=$245.13
INFO:plugins.stocks.services:✅ Showcase update complete: 8 successful, 0 failed
INFO:plugins.stocks.plugin:✅ [SERVICE] Showcase prices update complete!
```

---

## What You'll See in Browser Console (Press F12)

### ❌ Current State (No Data):
```javascript
🔄 [SHOWCASE] Starting refresh...
🔄 [SHOWCASE] Fetching from /api/v1/plugins/stocks/showcase
🔄 [SHOWCASE] Response status: 200
📊 [SHOWCASE] Received data: {status: "success", quotes: Array(8)}
📊 [SHOWCASE] Number of quotes: 8
📈 [SHOWCASE] Processing AAPL: {symbol: "AAPL", target: null, direction: null, enabled: 1, price: null, high: null, low: null, price_ts: null, pred_next: null, src_days: null, pred_ts: null}

🔍 [SHOWCASE DEBUG] AAPL RAW VALUES: {
    price: null,
    priceType: "object",  ← null is type "object" in JavaScript!
    high: null,
    highType: "object",
    low: null,
    lowType: "object",
    timestamp: null
}

⚠️ [SHOWCASE DEBUG] AAPL price NOT updated: {
    priceCellExists: true,         ← Cell exists
    priceValue: null,               ← But value is null
    priceIsNull: true,              ← Null check fails
    priceIsUndefined: false,
    currentCellText: "--"           ← Stays as "--"
}

⚠️ [SHOWCASE DEBUG] AAPL high NOT updated: {
    highCellExists: true,
    highValue: null,
    highIsNull: true,
    currentCellText: "--"
}

⚠️ [SHOWCASE DEBUG] AAPL low NOT updated: {
    lowCellExists: true,
    lowValue: null,
    lowIsNull: true,
    currentCellText: "--"
}

⚠️ [SHOWCASE DEBUG] AAPL timestamp NOT updated: {
    tsCellExists: true,
    timestampValue: null,
    currentCellText: "--"
}

❌ [SHOWCASE DEBUG] AAPL - NO UPDATES APPLIED! Cell stays as "--" {
    quote: {symbol: "AAPL", price: null, high: null, low: null, ...},
    cells: {
        price: "--",  ← All cells still show "--"
        high: "--",
        low: "--",
        ts: "--"
    }
}

... (repeat for all 8 symbols)

✅ [SHOWCASE] Update complete: 0 updated, 8 skipped
```

### ✅ After Starting Service (With Data):
```javascript
🔄 [SHOWCASE] Starting refresh...
📊 [SHOWCASE] Received data: {status: "success", quotes: Array(8)}
📈 [SHOWCASE] Processing AAPL: {symbol: "AAPL", price: 247.45, high: 249.04, low: 245.13, price_ts: "2025-10-16 16:52:18"}

🔍 [SHOWCASE DEBUG] AAPL RAW VALUES: {
    price: 247.45,            ← Now has value!
    priceType: "number",      ← Type is number (good!)
    high: 249.04,
    highType: "number",
    low: 245.13,
    lowType: "number",
    timestamp: "2025-10-16 16:52:18"
}

💲 [SHOWCASE] AAPL price: -- → $247.45     ← Updated!
📈 [SHOWCASE] AAPL high: -- → $249.04       ← Updated!
📉 [SHOWCASE] AAPL low: -- → $245.13        ← Updated!
🕒 [SHOWCASE] AAPL timestamp: -- → 4:52:18 PM  ← Updated!

... (repeat for all 8 symbols)

✅ [SHOWCASE] Update complete: 8 updated, 0 skipped  ← Success!
```

---

## How to Test Right Now

### Option 1: See Current State (Before Starting Service)
1. Go to: http://127.0.0.1:8000/api/v1/plugins/stocks/
2. Press **F12** to open browser console
3. Click **"🔄 Refresh"** button in Market Showcase
4. Watch the console output - you'll see all the debug info above
5. Check PowerShell terminal - you'll see the backend logs

**Expected:** All cells show "--", debug logs explain why (null values)

### Option 2: Start Service and See It Work
1. Click **"▶️ Start Service"** button
2. Watch PowerShell terminal for:
   ```
   🔄 [SERVICE] Starting monitoring cycle #1
   📊 [SERVICE] Starting showcase price update...
   ```
3. Wait for:
   ```
   ✅ [SERVICE] Showcase prices update complete!
   ```
4. Click **"🔄 Refresh"** in Market Showcase (or wait 30 seconds)
5. Watch browser console show successful updates
6. See "--" change to "$247.45" on the page!

---

## Debug Log Categories

### Backend (PowerShell Terminal):

| Prefix | Category | What It Shows |
|--------|----------|---------------|
| `🔄 [SERVICE]` | Background Service | Monitoring cycles, timing, service lifecycle |
| `📊` | API Fetching | Finnhub/Alpha Vantage API calls |
| `🔵` | Finnhub API | Primary API responses |
| `🟡` | Alpha Vantage | Fallback API responses |
| `💾 [DATABASE]` | Data Storage | INSERT operations with verification |
| `📊 [GUI UPDATE]` | Data Preparation | Service layer preparing data for endpoint |
| `🌐 [ENDPOINT]` | HTTP Endpoint | /showcase route handling requests |
| `✅` | Success | Operations completed successfully |
| `⚠️` | Warning | Non-critical issues (empty data, skipped operations) |
| `❌` | Error | Critical failures |

### Frontend (Browser Console):

| Prefix | Category | What It Shows |
|--------|----------|---------------|
| `🔄 [SHOWCASE]` | Fetch Operation | HTTP requests to backend |
| `📊 [SHOWCASE]` | Data Receipt | Response data structure |
| `📈 [SHOWCASE]` | Symbol Processing | Per-symbol data handling |
| `🔍 [SHOWCASE DEBUG]` | Debug Details | Raw values, types, conditions |
| `💲 [SHOWCASE]` | Price Update | Successful DOM updates |
| `⚠️ [SHOWCASE DEBUG]` | Skipped Update | Why update was skipped (null value, missing element) |
| `❌ [SHOWCASE DEBUG]` | Update Failed | Complete failure analysis |
| `✅ [SHOWCASE]` | Summary | Total updated vs skipped |

---

## Quick Troubleshooting

### Problem: See this in terminal?
```
⚠️ [ENDPOINT] WARNING: latest_prices table is EMPTY!
❌ NO DATA | Price=$None
```
**Solution:** Start the service! Click "▶️ Start Service"

---

### Problem: See this in browser console?
```
⚠️ [SHOWCASE DEBUG] AAPL price NOT updated: {priceIsNull: true}
```
**Solution:** Backend has no data. Start the service!

---

### Problem: Service started but still no prices?
**Check terminal for:**
```
❌ Finnhub HTTP 401 for AAPL
❌❌ Failed to fetch quote for AAPL from all sources
```
**Solution:** Check API keys in `.env` file

---

### Problem: Some stocks have data, others don't?
**Check terminal for:**
```
⚠️ No data returned for TSLA
✅ Updated AAPL: $247.45
```
**Solution:** API might be throttling. Wait for next cycle.

---

## Summary

With these enhanced debug logs, you can now:

✅ **See exactly what the backend sends** (null vs actual values)
✅ **See exactly what the frontend receives** (type checking, value inspection)
✅ **Know why cells stay as "--"** (explicit null/undefined checks)
✅ **Track the complete data flow** (API → Database → Endpoint → Frontend → DOM)
✅ **Diagnose issues immediately** (service not started, API errors, rate limiting)

**The debugging is now foolproof! Every decision point is logged with complete context.** 🎯
