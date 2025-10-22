"""
Stock price prediction module using historical data.
"""
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class StockPredictor:
    """Stock price prediction using various algorithms."""
    
    def __init__(self, alpha_vantage_key: str, finnhub_key: str = ""):
        """
        Initialize predictor with API keys.
        Uses Alpha Vantage for historical data (predictions only).
        Finnhub key kept for compatibility (not used in predictor).
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.finnhub_key = finnhub_key  # Not used, kept for compatibility
    
    async def fetch_historical_data(self, symbol: str, days: int = 10) -> Optional[List[Dict]]:
        """Fetch historical daily data for the symbol using Alpha Vantage (FREE)."""
        symbol = symbol.upper()
        logger.info(f"📈 Fetching {days} days of historical data for {symbol} from Alpha Vantage")
        
        if not self.alpha_vantage_key:
            logger.warning("⚠️ Alpha Vantage API key not configured")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use Alpha Vantage TIME_SERIES_DAILY endpoint (FREE tier)
                async with session.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "TIME_SERIES_DAILY",
                        "symbol": symbol,
                        "apikey": self.alpha_vantage_key,
                        "outputsize": "compact"  # Last 100 days
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"❌ Alpha Vantage API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    # Check for error messages
                    if "Error Message" in data:
                        logger.error(f"❌ Alpha Vantage error: {data['Error Message']}")
                        return None
                    
                    if "Note" in data:
                        logger.warning(f"⚠️ Alpha Vantage rate limit: {data['Note']}")
                        return None
                    
                    # Parse Alpha Vantage data
                    # Data format: {"Time Series (Daily)": {"2025-10-20": {"1. open": "...", "2. high": "...", ...}}}
                    time_series = data.get("Time Series (Daily)", {})
                    
                    if not time_series:
                        logger.error(f"❌ Alpha Vantage returned no data for {symbol}")
                        return None
                    
                    # Convert to list of dicts, sorted by date (newest first)
                    historical = []
                    for date_str in sorted(time_series.keys(), reverse=True)[:days]:
                        day_data = time_series[date_str]
                        historical.append({
                            'date': date_str,
                            'open': float(day_data.get('1. open', 0)),
                            'high': float(day_data.get('2. high', 0)),
                            'low': float(day_data.get('3. low', 0)),
                            'close': float(day_data.get('4. close', 0)),
                            'volume': int(day_data.get('5. volume', 0))
                        })
                    
                    logger.info(f"✅ Fetched {len(historical)} days of data for {symbol} from Alpha Vantage")
                    return historical
        
        except Exception as e:
            logger.error(f"❌ Error fetching historical data: {e}", exc_info=True)
            return None
    
    def calculate_moving_average(self, prices: List[float], window: int) -> float:
        """Calculate simple moving average."""
        if len(prices) < window:
            window = len(prices)
        return sum(prices[-window:]) / window
    
    def calculate_exponential_moving_average(self, prices: List[float], window: int) -> float:
        """Calculate exponential moving average (EMA)."""
        if not prices:
            return 0.0
        
        if len(prices) < window:
            # For insufficient data, use simple average
            return sum(prices) / len(prices)
        
        multiplier = 2 / (window + 1)
        ema = prices[0]  # Start with first price
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def linear_regression_predict(self, prices: List[float], days_ahead: int = 15) -> List[float]:
        """
        Predict future prices using linear regression.
        
        Args:
            prices: Historical closing prices (oldest to newest)
            days_ahead: Number of days to predict into the future
        
        Returns:
            List of predicted prices for the next N days
        """
        if len(prices) < 2:
            return [prices[-1]] * days_ahead if prices else [0.0] * days_ahead
        
        # Prepare data for linear regression
        n = len(prices)
        x = np.arange(n)
        y = np.array(prices)
        
        # Calculate slope (m) and intercept (b) for y = mx + b
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return [prices[-1]] * days_ahead
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Predict future prices
        predictions = []
        for i in range(days_ahead):
            future_x = n + i
            predicted_price = slope * future_x + intercept
            # Ensure price doesn't go negative
            predicted_price = max(0.01, predicted_price)
            predictions.append(predicted_price)
        
        return predictions
    
    def weighted_moving_average_predict(self, prices: List[float], days_ahead: int = 15) -> List[float]:
        """
        Predict using weighted moving average with trend analysis.
        
        Args:
            prices: Historical closing prices
            days_ahead: Number of days to predict
        
        Returns:
            List of predicted prices
        """
        if len(prices) < 3:
            return [prices[-1]] * days_ahead if prices else [0.0] * days_ahead
        
        # Calculate short and long term trends
        short_ma = self.calculate_moving_average(prices, min(3, len(prices)))
        long_ma = self.calculate_moving_average(prices, min(7, len(prices)))
        
        # Calculate trend (momentum)
        trend = (short_ma - long_ma) / long_ma if long_ma > 0 else 0
        
        # Calculate recent volatility
        recent_prices = prices[-5:] if len(prices) >= 5 else prices
        volatility = np.std(recent_prices) if len(recent_prices) > 1 else 0
        
        predictions = []
        last_price = prices[-1]
        
        for i in range(days_ahead):
            # Apply trend with dampening (trend effect decreases over time)
            dampening = 0.95 ** i  # Exponential decay
            predicted_change = trend * dampening
            
            # Add small random variation based on volatility
            variation = np.random.normal(0, volatility * 0.1)
            
            predicted_price = last_price * (1 + predicted_change + variation)
            predicted_price = max(0.01, predicted_price)  # Ensure positive
            
            predictions.append(predicted_price)
            last_price = predicted_price
        
        return predictions
    
    def ensemble_predict(self, prices: List[float], days_ahead: int = 15) -> Tuple[List[float], Dict]:
        """
        Ensemble prediction combining multiple methods.
        
        Returns:
            Tuple of (predictions, metadata)
        """
        if not prices:
            return [0.0] * days_ahead, {'error': 'No historical data'}
        
        # Get predictions from different methods
        linear_pred = self.linear_regression_predict(prices, days_ahead)
        wma_pred = self.weighted_moving_average_predict(prices, days_ahead)
        
        # Calculate EMA-based prediction
        ema_short = self.calculate_exponential_moving_average(prices, min(3, len(prices)))
        ema_long = self.calculate_exponential_moving_average(prices, min(7, len(prices)))
        ema_trend = (ema_short - ema_long) / ema_long if ema_long > 0 else 0
        
        # Combine predictions with weights
        # Linear regression: 40%, WMA: 40%, EMA trend: 20%
        ensemble_predictions = []
        last_price = prices[-1]
        
        for i in range(days_ahead):
            linear_weight = 0.4
            wma_weight = 0.4
            ema_weight = 0.2
            
            ema_prediction = last_price * (1 + ema_trend * (0.95 ** i))
            
            combined = (
                linear_pred[i] * linear_weight +
                wma_pred[i] * wma_weight +
                ema_prediction * ema_weight
            )
            
            ensemble_predictions.append(max(0.01, combined))
            last_price = combined
        
        # Calculate confidence metrics
        metadata = {
            'method': 'ensemble',
            'base_price': prices[-1],
            'price_change': ((ensemble_predictions[-1] - prices[-1]) / prices[-1] * 100),
            'trend': 'bullish' if ensemble_predictions[-1] > prices[-1] else 'bearish',
            'volatility': float(np.std(prices[-5:]) if len(prices) >= 5 else 0),
            'data_points': len(prices)
        }
        
        return ensemble_predictions, metadata
    
    async def predict_stock(self, symbol: str, historical_days: int = 10, 
                           prediction_days: int = 15) -> Optional[Dict]:
        """
        Main prediction function.
        
        Args:
            symbol: Stock symbol
            historical_days: Number of historical days to use
            prediction_days: Number of days to predict ahead
        
        Returns:
            Dictionary with predictions and metadata
        """
        # Fetch historical data
        historical = await self.fetch_historical_data(symbol, historical_days)
        
        if not historical:
            logger.error(f"❌ Could not fetch historical data for {symbol}")
            return None
        
        # Extract closing prices
        closing_prices = [day['close'] for day in reversed(historical)]
        
        # Generate predictions
        predictions, metadata = self.ensemble_predict(closing_prices, prediction_days)
        
        # Build prediction dates
        last_date = datetime.strptime(historical[0]['date'], '%Y-%m-%d')
        prediction_dates = []
        for i in range(1, prediction_days + 1):
            next_date = last_date + timedelta(days=i)
            # Skip weekends (assuming market is closed)
            while next_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                next_date += timedelta(days=1)
            prediction_dates.append(next_date.strftime('%Y-%m-%d'))
        
        result = {
            'symbol': symbol,
            'historical_days': len(closing_prices),
            'prediction_days': prediction_days,
            'historical_data': [
                {'date': day['date'], 'close': day['close']} 
                for day in reversed(historical)
            ],
            'predictions': [
                {'date': date, 'predicted_price': round(price, 2)}
                for date, price in zip(prediction_dates, predictions)
            ],
            'metadata': metadata,
            'summary': {
                'current_price': closing_prices[-1],
                'final_predicted_price': round(predictions[-1], 2),  # Add for frontend compatibility
                'predicted_price_15d': round(predictions[-1], 2),
                'expected_change': round(metadata['price_change'], 2),
                'trend': metadata['trend'],
                'confidence': self._calculate_confidence(closing_prices, predictions[0])
            }
        }
        
        logger.info(f"✅ Generated {prediction_days}-day prediction for {symbol}")
        logger.info(f"   Current: ${closing_prices[-1]:.2f} → Predicted (15d): ${predictions[-1]:.2f} ({metadata['price_change']:.2f}%)")
        
        return result
    
    def _calculate_confidence(self, historical: List[float], first_prediction: float) -> str:
        """Calculate confidence level based on volatility and trend consistency."""
        if len(historical) < 3:
            return "low"
        
        # Calculate volatility
        volatility = np.std(historical) / np.mean(historical)
        
        # Calculate trend consistency
        increases = sum(1 for i in range(1, len(historical)) if historical[i] > historical[i-1])
        consistency = increases / (len(historical) - 1)
        
        # Determine confidence
        if volatility < 0.02 and abs(consistency - 0.5) > 0.3:
            return "high"
        elif volatility < 0.05:
            return "medium"
        else:
            return "low"
