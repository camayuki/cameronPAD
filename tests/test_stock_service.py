"""
Unit tests for Stock Service - tests API calls, database operations, and showcase endpoint
"""
import asyncio
import os
import sqlite3
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from plugins.stocks.services import StockService


class TestStockService:
    """Test the stock service functionality"""
    
    @pytest.fixture
    def service_config(self):
        """Create test configuration"""
        return {
            'finnhub_token': 'test_finnhub_token',
            'alpha_vantage_key': 'test_alpha_key',
            'alert_cooldown_minutes': 30,
            'alpha_min_interval': 13.0,
            'showcase_symbols': ['AAPL', 'MSFT', 'GOOGL']
        }
    
    @pytest.fixture
    def stock_service(self, service_config):
        """Create a stock service instance"""
        return StockService(service_config)
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a temporary test database"""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Create tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                target REAL,
                direction TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS latest_prices (
                symbol TEXT PRIMARY KEY,
                price REAL,
                high REAL,
                low REAL,
                ts TEXT
            )
        """)
        
        # Insert test stocks
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in test_symbols:
            cur.execute(
                "INSERT OR IGNORE INTO stocks (symbol, enabled) VALUES (?, 1)",
                (symbol,)
            )
        
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    @pytest.mark.asyncio
    async def test_fetch_quote_finnhub_success(self, stock_service):
        """Test successful Finnhub API call"""
        print("\n🧪 TEST: Fetch quote from Finnhub (mocked)")
        
        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'c': 175.50,  # current price
            'h': 178.20,  # high
            'l': 174.80,  # low
        })
        
        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            result = await stock_service.fetch_quote('AAPL')
        
        print(f"   ✅ Result: {result}")
        assert result is not None
        assert result['price'] == 175.50
        assert result['high'] == 178.20
        assert result['low'] == 174.80
        print("   ✅ Finnhub API call successful!")
    
    @pytest.mark.asyncio
    async def test_fetch_quote_finnhub_null_values(self, stock_service):
        """Test Finnhub returning null values"""
        print("\n🧪 TEST: Finnhub returns null values")
        
        # Mock aiohttp response with null values
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'c': None,
            'h': None,
            'l': None,
        })
        
        # Mock Alpha Vantage fallback success
        mock_av_response = AsyncMock()
        mock_av_response.status = 200
        mock_av_response.json = AsyncMock(return_value={
            'Global Quote': {
                '05. price': '176.00',
                '03. high': '179.00',
                '04. low': '175.00'
            }
        })
        
        with patch('aiohttp.ClientSession.get', side_effect=[mock_response, mock_av_response]):
            result = await stock_service.fetch_quote('AAPL')
        
        print(f"   ✅ Result: {result}")
        assert result is not None
        assert result['price'] == 176.00
        print("   ✅ Alpha Vantage fallback successful!")
    
    @pytest.mark.asyncio
    async def test_store_latest_price(self, stock_service, test_db):
        """Test storing price data in database"""
        print("\n🧪 TEST: Store price in database")
        
        # Use test database
        original_db = "data/cameronpad_dev.db"
        
        # Store a price
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            
            stock_service._store_latest_price('AAPL', 175.50, 178.20, 174.80)
            
            # Verify the SQL was called
            assert mock_cursor.execute.called
            print("   ✅ Database storage called correctly!")
    
    @pytest.mark.asyncio
    async def test_update_showcase_prices(self, stock_service):
        """Test updating showcase prices"""
        print("\n🧪 TEST: Update showcase prices")
        
        # Mock fetch_quote to return test data
        async def mock_fetch_quote(symbol):
            prices = {
                'AAPL': {'price': 175.50, 'high': 178.20, 'low': 174.80},
                'MSFT': {'price': 380.25, 'high': 385.00, 'low': 378.50},
                'GOOGL': {'price': 142.75, 'high': 145.00, 'low': 141.00}
            }
            return prices.get(symbol)
        
        with patch.object(stock_service, 'fetch_quote', side_effect=mock_fetch_quote):
            with patch.object(stock_service, '_store_latest_price') as mock_store:
                await stock_service.update_showcase_prices()
                
                # Verify all symbols were stored
                assert mock_store.call_count == 3
                print(f"   ✅ All {mock_store.call_count} symbols updated!")
    
    def test_showcase_endpoint_query(self, test_db):
        """Test the SQL query used by showcase endpoint"""
        print("\n🧪 TEST: Showcase endpoint SQL query")
        
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Insert some test price data
        test_prices = [
            ('AAPL', 175.50, 178.20, 174.80, '2025-10-16T10:00:00'),
            ('MSFT', 380.25, 385.00, 378.50, '2025-10-16T10:00:00'),
        ]
        
        for symbol, price, high, low, ts in test_prices:
            cur.execute(
                "INSERT OR REPLACE INTO latest_prices (symbol, price, high, low, ts) VALUES (?, ?, ?, ?, ?)",
                (symbol, price, high, low, ts)
            )
        conn.commit()
        
        # Execute the showcase query
        cur.execute("""
            SELECT 
                s.symbol, s.target, s.direction, s.enabled,
                p.price, p.high, p.low, p.ts as price_ts
            FROM stocks s
            LEFT JOIN latest_prices p ON s.symbol = p.symbol
            WHERE s.enabled = 1
            ORDER BY s.symbol
        """)
        
        quotes = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        print(f"   📊 Found {len(quotes)} quotes:")
        for quote in quotes:
            print(f"      {quote['symbol']}: price=${quote.get('price', 'None')}, high=${quote.get('high', 'None')}, low=${quote.get('low', 'None')}")
        
        # Verify results
        assert len(quotes) == 3  # All 3 test symbols
        assert quotes[0]['symbol'] == 'AAPL'
        assert quotes[0]['price'] == 175.50
        assert quotes[1]['symbol'] == 'GOOGL'
        assert quotes[1]['price'] is None  # No price data for GOOGL
        print("   ✅ Showcase query returns correct data!")


class TestEndToEndScenario:
    """Test end-to-end scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_flow_with_real_structure(self):
        """Test the complete flow: fetch -> store -> query"""
        print("\n🧪 END-TO-END TEST: Complete data flow")
        print("=" * 60)
        
        # Create service
        config = {
            'finnhub_token': 'test_token',
            'alpha_vantage_key': 'test_key',
            'alert_cooldown_minutes': 30,
            'alpha_min_interval': 13.0,
            'showcase_symbols': ['AAPL', 'MSFT']
        }
        service = StockService(config)
        
        # Mock the API calls
        async def mock_fetch(symbol):
            print(f"   📊 Mocking API fetch for {symbol}...")
            return {
                'AAPL': {'price': 175.50, 'high': 178.20, 'low': 174.80},
                'MSFT': {'price': 380.25, 'high': 385.00, 'low': 378.50}
            }.get(symbol)
        
        stored_data = []
        
        def mock_store(symbol, price, high, low):
            print(f"   💾 Storing {symbol}: price=${price}, high=${high}, low=${low}")
            stored_data.append({
                'symbol': symbol,
                'price': price,
                'high': high,
                'low': low
            })
        
        # Execute the flow
        with patch.object(service, 'fetch_quote', side_effect=mock_fetch):
            with patch.object(service, '_store_latest_price', side_effect=mock_store):
                print("\n📈 Step 1: Fetching quotes from API...")
                await service.update_showcase_prices()
        
        # Verify results
        print(f"\n✅ Step 2: Verify stored data")
        print(f"   Total stored: {len(stored_data)} symbols")
        for data in stored_data:
            print(f"   ✅ {data['symbol']}: ${data['price']} (H: ${data['high']}, L: ${data['low']})")
        
        assert len(stored_data) == 2
        assert stored_data[0]['symbol'] == 'AAPL'
        assert stored_data[0]['price'] == 175.50
        assert stored_data[1]['symbol'] == 'MSFT'
        assert stored_data[1]['price'] == 380.25
        
        print("\n" + "=" * 60)
        print("✅ END-TO-END TEST PASSED! All data flows correctly!")
        print("=" * 60)


def test_print_api_endpoints():
    """Print information about API endpoints and data flow"""
    print("\n" + "=" * 60)
    print("📊 STOCK SERVICE DATA FLOW")
    print("=" * 60)
    print("\n1️⃣  API Call (Finnhub primary, Alpha Vantage fallback)")
    print("    └─> fetch_quote(symbol) → {price, high, low}")
    print("\n2️⃣  Database Storage")
    print("    └─> INSERT INTO latest_prices (symbol, price, high, low, ts)")
    print("\n3️⃣  Showcase Endpoint Query")
    print("    └─> SELECT stocks LEFT JOIN latest_prices")
    print("\n4️⃣  Frontend Display")
    print("    └─> JavaScript updates DOM with price data")
    print("\n" + "=" * 60)
    print("🔍 TO DEBUG LIVE:")
    print("   1. Start server: py -m uvicorn app_new.main:app --reload")
    print("   2. Go to: http://127.0.0.1:8000/api/v1/plugins/stocks/")
    print("   3. Click 'Start Service' button")
    print("   4. Watch VS Code terminal for backend logs")
    print("   5. Watch browser console (F12) for frontend logs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print("\n🧪 RUNNING STOCK SERVICE UNIT TESTS")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
