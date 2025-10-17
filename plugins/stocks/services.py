"""
Stock service for data fetching and business logic.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import aiohttp

from .models import Stock, Alert, LatestPrice, Prediction

logger = logging.getLogger(__name__)


class StockService:
    """Service for stock data operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.finnhub_token = config.get('finnhub_token')
        self.alpha_vantage_key = config.get('alpha_vantage_key')
        self.cooldown_minutes = config.get('alert_cooldown_minutes', 0)
        self.last_alpha_call = 0.0
        self.alpha_min_interval = config.get('alpha_min_interval', 13.0)
        
        # Alert cooldown tracking
        self.last_alerts: Dict[str, float] = {}
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to external APIs."""
        results = {}
        
        if self.finnhub_token:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://finnhub.io/api/v1/quote",
                        params={"symbol": "AAPL", "token": self.finnhub_token},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            results['finnhub'] = 'connected'
                        else:
                            results['finnhub'] = f'error: {response.status}'
            except Exception as e:
                results['finnhub'] = f'error: {str(e)}'
        else:
            results['finnhub'] = 'not_configured'
        
        if self.alpha_vantage_key:
            try:
                # Rate limit Alpha Vantage calls
                await self._alpha_rate_limit()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": "AAPL",
                            "apikey": self.alpha_vantage_key
                        },
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        if response.status == 200:
                            results['alpha_vantage'] = 'connected'
                        else:
                            results['alpha_vantage'] = f'error: {response.status}'
            except Exception as e:
                results['alpha_vantage'] = f'error: {str(e)}'
        else:
            results['alpha_vantage'] = 'not_configured'
        
        return results
    
    async def fetch_quote(self, symbol: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Fetch current quote for a symbol."""
        symbol = symbol.upper()
        logger.info(f"📊 Fetching quote for {symbol}...")
        logger.info(f"🔑 API Keys configured: Finnhub={'Yes' if self.finnhub_token else 'NO'}, AlphaVantage={'Yes' if self.alpha_vantage_key else 'NO'}")
        
        # Try Finnhub first
        if self.finnhub_token:
            try:
                logger.info(f"🔵 Trying Finnhub API for {symbol}...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://finnhub.io/api/v1/quote",
                        params={"symbol": symbol, "token": self.finnhub_token},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        logger.info(f"🔵 Finnhub response status for {symbol}: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"🔵 Finnhub data for {symbol}: {data}")
                            price = data.get("c")  # current price
                            high = data.get("h")   # high
                            low = data.get("l")    # low
                            
                            if any(v is not None for v in (price, high, low)):
                                logger.info(f"✅ Finnhub success for {symbol}: price=${price}, high=${high}, low=${low}")
                                return (
                                    float(price) if price is not None else None,
                                    float(high) if high is not None else None,
                                    float(low) if low is not None else None
                                )
                            else:
                                logger.warning(f"⚠️ Finnhub returned null values for {symbol}")
                        else:
                            logger.error(f"❌ Finnhub HTTP {response.status} for {symbol}")
                            response_text = await response.text()
                            logger.error(f"❌ Finnhub response body: {response_text[:200]}")
            except Exception as e:
                logger.error(f"❌ Finnhub API error for {symbol}: {type(e).__name__}: {e}")
                logger.error(f"❌ Finnhub full error details:", exc_info=True)
        
        # Fallback to Alpha Vantage
        if self.alpha_vantage_key:
            try:
                logger.info(f"🟡 Falling back to Alpha Vantage for {symbol}...")
                await self._alpha_rate_limit()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "GLOBAL_QUOTE",
                            "symbol": symbol,
                            "apikey": self.alpha_vantage_key
                        },
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as response:
                        logger.debug(f"🟡 Alpha Vantage response status for {symbol}: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            logger.debug(f"🟡 Alpha Vantage data for {symbol}: {data}")
                            quote = data.get("Global Quote", {})
                            price = quote.get("05. price")
                            high = quote.get("03. high")
                            low = quote.get("04. low")
                            
                            if price or high or low:
                                logger.info(f"✅ Alpha Vantage success for {symbol}: price=${price}, high=${high}, low=${low}")
                                return (
                                    float(price) if price else None,
                                    float(high) if high else None,
                                    float(low) if low else None
                                )
                            else:
                                logger.error(f"⚠️ Alpha Vantage returned empty quote for {symbol}")
                                logger.error(f"⚠️ Alpha Vantage response data: {data}")
                        else:
                            logger.error(f"❌ Alpha Vantage HTTP {response.status} for {symbol}")
                            response_text = await response.text()
                            logger.error(f"❌ Alpha Vantage response body: {response_text[:200]}")
            except Exception as e:
                logger.error(f"❌ Alpha Vantage API error for {symbol}: {type(e).__name__}: {e}")
                logger.error(f"❌ Alpha Vantage full error details:", exc_info=True)
        
        logger.error(f"❌❌ Failed to fetch quote for {symbol} from all sources")
        return (None, None, None)
    
    async def _alpha_rate_limit(self) -> None:
        """Apply rate limiting for Alpha Vantage API."""
        current_time = time.time()
        time_since_last = current_time - self.last_alpha_call
        
        if time_since_last < self.alpha_min_interval:
            wait_time = self.alpha_min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_alpha_call = time.time()
    
    async def update_tracked_stocks(self, db_path: str = "data/cameronpad_dev.db") -> None:
        """Update prices for all tracked stocks."""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all enabled stocks
        cursor.execute("SELECT symbol FROM stocks WHERE enabled = 1")
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not symbols:
            return
        
        logger.info(f"Updating prices for {len(symbols)} symbols")
        
        # Fetch quotes with concurrency control
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def fetch_and_store(symbol: str):
            async with semaphore:
                price, high, low = await self.fetch_quote(symbol)
                if price is not None or high is not None or low is not None:
                    await self._store_latest_price(symbol, price, high, low, db_path)
        
        tasks = [fetch_and_store(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _store_latest_price(self, symbol: str, price: Optional[float], 
                                high: Optional[float], low: Optional[float], 
                                db_path: str = "data/cameronpad_dev.db") -> None:
        """Store latest price data."""
        import sqlite3
        
        if price is None and high is None and low is None:
            logger.debug(f"⚠️ Skipping store for {symbol} - all values are None")
            return
        
        logger.info(f"💾 [DATABASE] Storing {symbol} → Price: ${price}, High: ${high}, Low: ${low}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Upsert latest price
        cursor.execute("""
            INSERT INTO latest_prices(symbol, price, high, low, ts)
            VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                price=COALESCE(excluded.price, price),
                high=COALESCE(excluded.high, high),
                low=COALESCE(excluded.low, low),
                ts=CURRENT_TIMESTAMP
        """, (symbol, price, high, low))
        conn.commit()
        
        # Verify the data was stored
        cursor.execute("SELECT price, high, low FROM latest_prices WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if row:
            logger.info(f"✅ [DATABASE] {symbol} stored successfully - Verified: Price=${row[0]}, High=${row[1]}, Low=${row[2]}")
        else:
            logger.error(f"❌ [DATABASE] Failed to verify {symbol} after INSERT")
        
        conn.close()
    
    async def check_alerts(self, db_path: str = "data/cameronpad_dev.db") -> List[Alert]:
        """Check for alert conditions and create alerts."""
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get stocks with their latest prices
        query = """
        SELECT s.id, s.symbol, s.target, s.direction, p.price
        FROM stocks s
        LEFT JOIN latest_prices p ON s.symbol = p.symbol
        WHERE s.enabled = 1 AND p.price IS NOT NULL
        """
        
        cursor.execute(query)
        triggered_alerts = []
        
        for row in cursor.fetchall():
            stock_id, symbol, target, direction, price = row
            
            # Check alert conditions
            alert_triggered = False
            if direction == 'above' and price >= target:
                alert_triggered = True
            elif direction == 'below' and price <= target:
                alert_triggered = True
            
            if alert_triggered:
                # Check cooldown
                if self._is_cooldown_active(symbol):
                    continue
                
                # Create alert
                alert = Alert(symbol, price, target, direction)
                cursor2 = conn.cursor()
                cursor2.execute("""
                    INSERT INTO alerts (symbol, price, target, direction, ts)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (symbol, price, target, direction))
                conn.commit()
                alert.id = cursor2.lastrowid
                
                triggered_alerts.append(alert)
                
                # Update cooldown
                self.last_alerts[symbol] = time.time()
                
                logger.info(f"Alert triggered: {symbol} ${price} {direction} ${target}")
        
        conn.close()
        
        # Send notifications if any alerts triggered
        if triggered_alerts:
            await self._send_alert_notifications(triggered_alerts)
        
        return triggered_alerts
    
    def _is_cooldown_active(self, symbol: str) -> bool:
        """Check if alert cooldown is active for a symbol."""
        if self.cooldown_minutes <= 0:
            return False
        
        if symbol not in self.last_alerts:
            return False
        
        elapsed_minutes = (time.time() - self.last_alerts[symbol]) / 60
        return elapsed_minutes < self.cooldown_minutes
    
    async def _send_alert_notifications(self, alerts: List[Alert]) -> None:
        """Send notifications for triggered alerts via SMS, Telegram, and Discord."""
        import os
        import requests
        
        # Get notification credentials from environment
        TWILIO_SID = os.getenv("TWILIO_SID")
        TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
        TWILIO_FROM = os.getenv("TWILIO_FROM")
        ALERT_PHONE = os.getenv("ALERT_PHONE")
        
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
        DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
        
        for alert in alerts:
            message = f"🚨 [CameronPAD] {alert.symbol} {alert.direction} ${alert.target:.2f} (current: ${alert.price:.2f})"
            logger.info(f"Notification: {message}")
            
            # Send SMS via Twilio
            if all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, ALERT_PHONE]):
                try:
                    requests.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
                        data={"From": TWILIO_FROM, "To": ALERT_PHONE, "Body": message},
                        auth=(TWILIO_SID, TWILIO_TOKEN),
                        timeout=10
                    )
                    logger.info(f"📱 SMS sent for {alert.symbol}")
                except Exception as e:
                    logger.error(f"❌ SMS error: {e}")
            
            # Send via Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
                        timeout=10
                    )
                    logger.info(f"📱 Telegram sent for {alert.symbol}")
                except Exception as e:
                    logger.error(f"❌ Telegram error: {e}")
            
            # Send via Discord
            if DISCORD_WEBHOOK_URL:
                try:
                    requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
                    logger.info(f"📱 Discord sent for {alert.symbol}")
                except Exception as e:
                    logger.error(f"❌ Discord error: {e}")
    
    async def get_showcase_symbols(self) -> List[str]:
        """Get symbols for showcase display."""
        showcase_symbols = self.config.get('showcase_symbols', [
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'SPY'
        ])
        return showcase_symbols
    
    async def ensure_showcase_symbols(self, db_path: str = "data/cameronpad_dev.db") -> None:
        """Ensure showcase symbols exist in the stocks table."""
        import sqlite3
        
        symbols = await self.get_showcase_symbols()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for symbol in symbols:
            # Insert showcase symbol if it doesn't exist
            cursor.execute("""
                INSERT OR IGNORE INTO stocks(symbol, target, direction, enabled)
                VALUES(?, 0, 'above', 1)
            """, (symbol,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Ensured {len(symbols)} showcase symbols in database")
    
    async def update_showcase_prices(self, db_path: str = "data/cameronpad_dev.db") -> None:
        """Update prices for showcase symbols."""
        symbols = await self.get_showcase_symbols()
        
        if not symbols:
            logger.warning("⚠️ No showcase symbols to update")
            return
        
        logger.info(f"📊 Updating showcase prices for {len(symbols)} symbols: {', '.join(symbols)}")
        
        # Fetch quotes with concurrency control
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests for showcase
        successful = 0
        failed = 0
        
        async def fetch_and_store(symbol: str):
            nonlocal successful, failed
            async with semaphore:
                try:
                    logger.debug(f"🔍 Starting fetch for {symbol}...")
                    price, high, low = await self.fetch_quote(symbol)
                    if price is not None or high is not None or low is not None:
                        logger.debug(f"💾 Storing {symbol} in database: price=${price}, high=${high}, low=${low}")
                        await self._store_latest_price(symbol, price, high, low, db_path)
                        logger.info(f"✅ Updated {symbol}: ${price}")
                        successful += 1
                    else:
                        logger.warning(f"⚠️ No data returned for {symbol}")
                        failed += 1
                except Exception as e:
                    logger.error(f"❌ Failed to update {symbol}: {e}", exc_info=True)
                    failed += 1
        
        tasks = [fetch_and_store(symbol) for symbol in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"✅ Showcase update complete: {successful} successful, {failed} failed")
    
    async def get_showcase_data(self, db_path: str = "data/cameronpad_dev.db") -> List[Dict[str, Any]]:
        """Get showcase data with latest prices."""
        import sqlite3
        
        logger.info("📊 [GUI UPDATE] get_showcase_data() called - preparing data for frontend")
        
        symbols = await self.get_showcase_symbols()
        logger.info(f"📊 [GUI UPDATE] Showcase symbols requested: {', '.join(symbols)}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, check what's in the database
        cursor.execute("SELECT COUNT(*) FROM latest_prices")
        total_prices = cursor.fetchone()[0]
        logger.info(f"📊 [GUI UPDATE] Database has {total_prices} total price records")
        
        # Get latest prices for showcase symbols
        placeholders = ','.join(['?' for _ in symbols])
        query = f"""
        SELECT symbol, price, high, low, ts
        FROM latest_prices
        WHERE symbol IN ({placeholders})
        """
        
        cursor.execute(query, tuple(symbols))
        rows = cursor.fetchall()
        conn.close()
        
        logger.info(f"📊 [GUI UPDATE] Query returned {len(rows)} price records for showcase symbols")
        
        prices_dict = {row[0]: {'symbol': row[0], 'price': row[1], 'high': row[2], 'low': row[3], 'ts': row[4]} for row in rows}
        
        # Log each symbol's data
        for symbol, data in prices_dict.items():
            logger.info(f"📈 [GUI UPDATE] {symbol}: Price=${data['price']}, High=${data['high']}, Low=${data['low']}, Time={data['ts']}")
        
        showcase_data = []
        for symbol in symbols:
            price_data = prices_dict.get(symbol, {})
            if symbol in prices_dict:
                logger.debug(f"✅ [GUI UPDATE] {symbol} has data - will send to frontend")
            else:
                logger.warning(f"⚠️ [GUI UPDATE] {symbol} has NO data - will send null values")
            
            showcase_data.append({
                'symbol': symbol,
                'price': price_data.get('price'),
                'high': price_data.get('high'),
                'low': price_data.get('low'),
                'timestamp': price_data.get('ts')
            })
        
        logger.info(f"📊 [GUI UPDATE] Prepared {len(showcase_data)} showcase records to send to frontend")
        logger.info(f"📊 [GUI UPDATE] Data summary: {sum(1 for d in showcase_data if d['price'] is not None)} with prices, {sum(1 for d in showcase_data if d['price'] is None)} without prices")
        
        return showcase_data
    
    def linear_regression_predict(self, values: List[float]) -> Optional[float]:
        """Simple linear regression prediction."""
        n = len(values)
        if n < 5:
            return None
        
        # Calculate linear regression
        x_sum = n * (n + 1) / 2
        xx_sum = n * (n + 1) * (2 * n + 1) / 6
        y_sum = sum(values)
        xy_sum = sum((i + 1) * v for i, v in enumerate(values))
        
        denominator = (n * xx_sum - x_sum * x_sum)
        if denominator == 0:
            return None
        
        slope = (n * xy_sum - x_sum * y_sum) / denominator
        intercept = (y_sum / n) - slope * (x_sum / n)
        
        # Predict next value
        next_prediction = intercept + slope * (n + 1)
        return next_prediction
    
    async def update_predictions(self, symbol: str) -> Optional[float]:
        """Update price predictions for a symbol using historical data."""
        if not self.finnhub_token:
            return None
        
        try:
            # Get historical daily data
            current_time = int(time.time())
            from_time = current_time - (60 * 60 * 24 * 40)  # 40 days ago
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://finnhub.io/api/v1/stock/candle",
                    params={
                        "symbol": symbol,
                        "resolution": "D",
                        "from": from_time,
                        "to": current_time,
                        "token": self.finnhub_token
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("s") == "ok":
                            closes = data.get("c", [])[-15:]  # Last 15 closing prices
                            
                            if len(closes) >= 5:
                                prediction = self.linear_regression_predict(closes)
                                
                                if prediction:
                                    # Store prediction
                                    import sqlite3
                                    
                                    conn = sqlite3.connect("data/cameronpad_dev.db")
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        INSERT INTO predictions(symbol, pred_next, src_days, ts)
                                        VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                                        ON CONFLICT(symbol) DO UPDATE SET
                                            pred_next=excluded.pred_next,
                                            src_days=excluded.src_days,
                                            ts=CURRENT_TIMESTAMP
                                    """, (symbol, prediction, len(closes)))
                                    conn.commit()
                                    conn.close()
                                    
                                    return prediction
        
        except Exception as e:
            logger.error(f"Error updating predictions for {symbol}: {e}")
        
        return None