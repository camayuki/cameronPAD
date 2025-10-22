# Stock Price Prediction Guide

## Overview
The stocks plugin now includes a **15-day stock price prediction** feature using machine learning algorithms based on historical data.

## How It Works

### Prediction Algorithm
The prediction system uses an **ensemble approach** combining three methods:

1. **Linear Regression (40% weight)**
   - Fits a straight line to historical prices
   - Extrapolates future trend

2. **Weighted Moving Average (40% weight)**
   - Analyzes short-term and long-term trends
   - Applies momentum-based prediction
   - Includes volatility dampening

3. **Exponential Moving Average (20% weight)**
   - Gives more weight to recent prices
   - Captures momentum changes

### Data Requirements
- **Historical Data**: Last 10 days (configurable)
- **Prediction Window**: 15 days ahead (configurable)
- **Data Source**: Alpha Vantage API (daily time series)

## API Endpoints

### 1. Get Detailed Prediction
```
GET /api/v1/plugins/stocks/predictions/{symbol}/detailed
```

**Parameters:**
- `symbol` (path): Stock symbol (e.g., AAPL, TSLA, MSFT)
- `historical_days` (query, optional): Number of days to analyze (default: 10)
- `prediction_days` (query, optional): Number of days to predict (default: 15)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/plugins/stocks/predictions/AAPL/detailed?historical_days=10&prediction_days=15"
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "historical_days": 10,
  "prediction_days": 15,
  "historical_data": [
    {"date": "2025-10-06", "close": 225.50},
    {"date": "2025-10-07", "close": 226.80},
    ...
  ],
  "predictions": [
    {"date": "2025-10-21", "predicted_price": 228.45},
    {"date": "2025-10-22", "predicted_price": 229.12},
    ...
    {"date": "2025-11-04", "predicted_price": 235.78}
  ],
  "metadata": {
    "method": "ensemble",
    "base_price": 227.30,
    "price_change": 3.73,
    "trend": "bullish",
    "volatility": 1.25,
    "data_points": 10
  },
  "summary": {
    "current_price": 227.30,
    "predicted_price_15d": 235.78,
    "expected_change": 3.73,
    "trend": "bullish",
    "confidence": "medium"
  }
}
```

### 2. Simple Prediction Update
```
POST /api/v1/plugins/stocks/predictions/{symbol}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/plugins/stocks/predictions/AAPL"
```

Updates the simple next-day prediction stored in the database.

## Response Fields

### Historical Data
- `date`: Trading date (YYYY-MM-DD)
- `close`: Closing price for that day

### Predictions
- `date`: Future date (skips weekends)
- `predicted_price`: Predicted closing price

### Metadata
- `method`: Prediction algorithm used ("ensemble")
- `base_price`: Current/last known price
- `price_change`: Expected % change over prediction period
- `trend`: "bullish" (up) or "bearish" (down)
- `volatility`: Recent price volatility measure
- `data_points`: Number of historical data points used

### Summary
- `current_price`: Latest closing price
- `predicted_price_15d`: Price predicted for day 15
- `expected_change`: Percentage change expected
- `trend`: Overall trend direction
- `confidence`: "high", "medium", or "low"
  - High: Low volatility + consistent trend
  - Medium: Moderate volatility
  - Low: High volatility or inconsistent trend

## Confidence Levels

The confidence calculation considers:
1. **Volatility**: Lower volatility = higher confidence
2. **Trend Consistency**: Consistent up/down trend = higher confidence
3. **Data Quality**: More data points = better predictions

### Interpretation
- **High**: Reliable prediction, stable stock behavior
- **Medium**: Reasonable prediction, moderate uncertainty
- **Low**: High uncertainty, volatile stock or insufficient data

## Usage Examples

### Python
```python
import requests

# Get 15-day prediction for Apple
response = requests.get(
    "http://localhost:8000/api/v1/plugins/stocks/predictions/AAPL/detailed",
    params={
        "historical_days": 10,
        "prediction_days": 15
    }
)

data = response.json()
print(f"Current: ${data['summary']['current_price']}")
print(f"Predicted (15d): ${data['summary']['predicted_price_15d']}")
print(f"Expected change: {data['summary']['expected_change']:.2f}%")
print(f"Confidence: {data['summary']['confidence']}")
```

### JavaScript
```javascript
async function getPrediction(symbol) {
    const response = await fetch(
        `/api/v1/plugins/stocks/predictions/${symbol}/detailed?historical_days=10&prediction_days=15`
    );
    const data = await response.json();
    
    console.log(`${symbol} Prediction:`);
    console.log(`Current: $${data.summary.current_price}`);
    console.log(`15-day: $${data.summary.predicted_price_15d}`);
    console.log(`Change: ${data.summary.expected_change}%`);
    console.log(`Trend: ${data.summary.trend}`);
}

getPrediction('AAPL');
```

## Limitations

1. **API Rate Limits**
   - Alpha Vantage free tier: 5 calls/minute, 500 calls/day
   - Predictions cached to reduce API calls

2. **Prediction Accuracy**
   - Predictions are **estimates** based on historical patterns
   - Actual market behavior may differ significantly
   - External events (news, earnings, etc.) not factored in

3. **Weekend Handling**
   - Predictions automatically skip weekends
   - Only predicts trading days

4. **Data Requirements**
   - Requires at least 2-3 days of historical data
   - More historical data = better predictions
   - Recommended: 10-30 days for optimal results

## Best Practices

1. **Use Multiple Symbols**: Compare predictions across similar stocks
2. **Check Confidence**: Higher confidence = more reliable
3. **Monitor Volatility**: High volatility = less reliable predictions
4. **Regular Updates**: Refresh predictions daily for best accuracy
5. **Combine with Analysis**: Use predictions alongside other analysis tools

## Error Handling

### Common Errors

**404 - Could not generate prediction**
- Alpha Vantage API key not configured
- Invalid stock symbol
- No historical data available

**Solution**: Check API key in `.env` file:
```env
ALPHA_VANTAGE_API_KEY=your_key_here
```

**429 - Rate Limit Exceeded**
- Too many API calls in short time
- Solution: Wait 60 seconds between predictions

## Configuration

Edit `plugins/stocks/config.yaml`:
```yaml
alpha_vantage_key: ${ALPHA_VANTAGE_API_KEY}
finnhub_token: ${FINNHUB_API_TOKEN}
alpha_min_interval: 13.0  # Minimum seconds between API calls
```

## Technical Details

### Algorithm Implementation
- **Location**: `plugins/stocks/predictor.py`
- **Integration**: `plugins/stocks/services.py`
- **API**: `plugins/stocks/api.py`

### Dependencies
- `numpy>=1.24.0`: Mathematical operations
- `aiohttp>=3.9.0`: Async HTTP requests
- `Alpha Vantage API`: Historical data source

## Future Enhancements

Planned features:
- [ ] Machine learning models (LSTM, Prophet)
- [ ] Sentiment analysis from news
- [ ] Multiple prediction algorithms to choose from
- [ ] Backtesting and accuracy metrics
- [ ] Intraday predictions (hourly/minute)
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)

---

**Disclaimer**: Stock predictions are for informational purposes only. This is not financial advice. Always do your own research before making investment decisions.
