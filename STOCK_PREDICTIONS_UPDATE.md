# Stock Predictions Feature - Updates

## Changes Made

### 1. Fixed Chart Display Issue
**Problem**: Chart wasn't displaying properly
**Solution**: 
- Changed canvas container to use fixed height (350px) with `position: relative`
- Updated Chart.js options to use `maintainAspectRatio: false` for better responsiveness
- Added proper container div with min-height to ensure chart has space
- Improved color handling with `.trim()` to avoid CSS variable whitespace issues

### 2. Added Detailed Algorithm Explanation Section

Added a comprehensive section that explains how the ensemble ML algorithm works:

#### Components Explained:

1. **Linear Regression (40% weight)**
   - Uses formula: `y = mx + b`
   - Best-fit line through historical prices
   - Identifies long-term trends
   - Best for stable, trending stocks

2. **Weighted Moving Average (40% weight)**
   - Short-term (3 days) vs long-term (7 days) momentum analysis
   - Exponential dampening to avoid over-prediction
   - Adapts to volatility patterns
   - Captures trend direction

3. **Exponential Moving Average (20% weight)**
   - Formula: `multiplier = 2/(n+1)`
   - More weight to recent prices
   - Reacts faster to price changes
   - Captures recent market sentiment

#### Final Formula:
```
Final_Prediction = (Linear_Regression × 0.40) + (Weighted_MA × 0.40) + (EMA_Trend × 0.20)
```

#### Confidence Levels:
- **HIGH**: Volatility < 2% (Green - most reliable)
- **MEDIUM**: Volatility 2-5% (Orange - moderate reliability)
- **LOW**: Volatility > 5% (Red - less reliable, high uncertainty)

### 3. Visual Improvements

- Added 3 colored cards explaining each algorithm component
- Formula display in monospace font with code-style background
- Confidence level indicators with color coding
- Better visual hierarchy and spacing
- Responsive grid layout that adapts to screen size

### 4. Chart Enhancements

- Proper responsive sizing
- Better tooltip formatting
- Improved grid lines and colors
- Fill areas under lines for better visualization
- Dashed line for predictions to distinguish from historical data
- Proper legend with point styles

## Testing Locally

1. **Start your Windows development server:**
   ```powershell
   cd D:\Repositories\cameronPAD_main2
   py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Access the stocks page:**
   ```
   http://127.0.0.1:8000/plugins/stocks
   ```

3. **Test predictions:**
   - Enter a symbol like `AAPL`
   - Select historical days (10, 30, or 60)
   - Click "Generate Forecast"
   - You should see:
     - Chart displaying properly
     - Detailed algorithm explanation section
     - Summary cards with metrics
     - Prediction table with 15 days

## Deploying to Linux Server

Once tested locally, deploy to your server:

```bash
# SSH to server
ssh root@ubuntu-2gb-ash-1

# Navigate to app directory
cd /opt/cameronpad

# Pull latest changes or upload files via WinSCP

# Restart the service (if using systemd)
systemctl restart cameronpad

# Or run manually
./venv/bin/uvicorn app_new.main:app --host 0.0.0.0 --port 8000
```

## How It Works

### Data Flow:
1. User enters stock symbol (e.g., AAPL) and clicks "Generate Forecast"
2. JavaScript calls: `GET /api/v1/plugins/stocks/predictions/AAPL/detailed?historical_days=10`
3. Backend (StockService) calls predictor with Alpha Vantage key
4. Predictor fetches last N days of historical data from Alpha Vantage
5. Runs ensemble algorithm:
   - Linear Regression prediction
   - Weighted MA prediction  
   - EMA trend prediction
   - Combines with weights: 40% + 40% + 20%
6. Returns JSON with:
   - Historical data
   - 15 predicted prices
   - Metadata (confidence, volatility, trend)
   - Summary stats
7. JavaScript renders:
   - Chart.js visualization
   - Summary cards
   - Prediction table
   - Algorithm explanation

### API Architecture:
- **Finnhub**: Real-time quotes for market showcase (FREE)
- **Alpha Vantage**: Historical daily data for predictions (FREE, 25 calls/day)

## Files Modified

1. **plugins/stocks/templates/stocks.html**
   - Added algorithm explanation section
   - Fixed chart container sizing
   - Improved Chart.js configuration
   - Added visual components for each algorithm

2. **plugins/stocks/predictor.py** (no changes needed)
   - Already implements the ensemble algorithm correctly

3. **plugins/stocks/services.py** (no changes needed)
   - Already configured with dual API keys

## Known Limitations

1. **Alpha Vantage Rate Limit**: 25 API calls per day (FREE tier)
   - Solution: Consider caching predictions or upgrading to paid tier
   
2. **Market Hours**: Historical data may lag by 1 day when markets are closed
   
3. **Prediction Accuracy**: ML predictions are estimates, not guarantees
   - Algorithm performs best on:
     - Stable, trending stocks
     - Low volatility periods
     - Longer historical data (30-60 days better than 10)

## Future Enhancements

- [ ] Add prediction caching to reduce API calls
- [ ] Add more algorithms (LSTM, Prophet, ARIMA)
- [ ] User-adjustable algorithm weights
- [ ] Save favorite predictions
- [ ] Prediction accuracy tracking over time
- [ ] Export predictions to CSV
- [ ] Compare multiple stocks side-by-side
