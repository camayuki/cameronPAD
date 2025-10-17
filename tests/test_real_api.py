"""
Test real API calls to verify we get actual stock data
"""
import asyncio
import aiohttp
import os
from datetime import datetime

# Set your API keys
FINNHUB_TOKEN = os.getenv('FINNHUB_TOKEN', 'd34g7shr01qqt8soved0d34g7shr01qqt8sovedg')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', 'I7TWLR7V5UPHL2AW')


async def test_finnhub_api():
    """Test real Finnhub API call"""
    print("\n" + "=" * 70)
    print("🔵 TESTING FINNHUB API (Primary)")
    print("=" * 70)
    
    symbol = 'AAPL'
    url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}'
    
    print(f"\n📡 Calling Finnhub API for {symbol}...")
    print(f"   URL: {url[:50]}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"   Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"\n📊 Raw Response Data:")
                    print(f"   {data}")
                    
                    price = data.get('c')  # current price
                    high = data.get('h')   # high
                    low = data.get('l')    # low
                    prev_close = data.get('pc')  # previous close
                    
                    print(f"\n💰 Parsed Stock Data for {symbol}:")
                    print(f"   Current Price: ${price}")
                    print(f"   High:          ${high}")
                    print(f"   Low:           ${low}")
                    print(f"   Prev Close:    ${prev_close}")
                    
                    if price and high and low:
                        print(f"\n✅ SUCCESS! Got real stock data from Finnhub")
                        print(f"   Price Range: ${low} - ${high}")
                        print(f"   Current: ${price}")
                        
                        # Sanity checks
                        if low <= price <= high:
                            print(f"   ✅ Price is within daily range (valid)")
                        else:
                            print(f"   ⚠️ Price outside daily range (check data)")
                        
                        if prev_close and abs(price - prev_close) / prev_close < 0.2:
                            print(f"   ✅ Price change from yesterday is reasonable (<20%)")
                        else:
                            print(f"   ⚠️ Large price change from yesterday")
                        
                        return True
                    else:
                        print(f"\n⚠️ WARNING: Got null values from Finnhub")
                        print(f"   This might mean:")
                        print(f"   - Market is closed")
                        print(f"   - Symbol not found")
                        print(f"   - API rate limit hit")
                        return False
                else:
                    print(f"\n❌ ERROR: HTTP {response.status}")
                    text = await response.text()
                    print(f"   Response: {text[:200]}")
                    return False
                    
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            return False


async def test_alpha_vantage_api():
    """Test real Alpha Vantage API call"""
    print("\n" + "=" * 70)
    print("🟡 TESTING ALPHA VANTAGE API (Fallback)")
    print("=" * 70)
    
    symbol = 'AAPL'
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
    
    print(f"\n📡 Calling Alpha Vantage API for {symbol}...")
    print(f"   URL: {url[:60]}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"   Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"\n📊 Raw Response Data:")
                    print(f"   {data}")
                    
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        price = float(quote.get('05. price', 0))
                        high = float(quote.get('03. high', 0))
                        low = float(quote.get('04. low', 0))
                        
                        print(f"\n💰 Parsed Stock Data for {symbol}:")
                        print(f"   Current Price: ${price}")
                        print(f"   High:          ${high}")
                        print(f"   Low:           ${low}")
                        
                        if price and high and low:
                            print(f"\n✅ SUCCESS! Got real stock data from Alpha Vantage")
                            print(f"   Price Range: ${low} - ${high}")
                            print(f"   Current: ${price}")
                            return True
                        else:
                            print(f"\n⚠️ WARNING: Got zero values")
                            return False
                    else:
                        print(f"\n⚠️ No 'Global Quote' in response")
                        if 'Note' in data:
                            print(f"   Note: {data['Note']}")
                            print(f"   This usually means: API rate limit reached (5 calls/min, 500/day)")
                        return False
                else:
                    print(f"\n❌ ERROR: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            return False


async def compare_with_web():
    """Show where to manually verify the prices"""
    print("\n" + "=" * 70)
    print("🌐 MANUAL VERIFICATION")
    print("=" * 70)
    print(f"\n📍 To verify the prices are real, check these URLs:")
    print(f"\n   Google Finance:")
    print(f"   https://www.google.com/finance/quote/AAPL:NASDAQ")
    print(f"\n   Yahoo Finance:")
    print(f"   https://finance.yahoo.com/quote/AAPL")
    print(f"\n   Finnhub (requires login):")
    print(f"   https://finnhub.io/quote/AAPL")
    print(f"\n   Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Note: If market is closed, you'll see yesterday's closing prices")


async def test_multiple_symbols():
    """Test multiple symbols to verify consistency"""
    print("\n" + "=" * 70)
    print("📊 TESTING MULTIPLE SYMBOLS")
    print("=" * 70)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    results = []
    
    for symbol in symbols:
        print(f"\n{'─' * 70}")
        print(f"Testing {symbol}...")
        
        url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}'
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get('c')
                        high = data.get('h')
                        low = data.get('l')
                        
                        if price and high and low:
                            print(f"✅ {symbol}: ${price} (Range: ${low} - ${high})")
                            results.append({
                                'symbol': symbol,
                                'price': price,
                                'high': high,
                                'low': low,
                                'valid': low <= price <= high
                            })
                        else:
                            print(f"⚠️ {symbol}: No data (null values)")
                    else:
                        print(f"❌ {symbol}: HTTP {response.status}")
                        
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
    
    if results:
        print(f"\n{'=' * 70}")
        print(f"📊 SUMMARY OF RESULTS")
        print(f"{'=' * 70}")
        print(f"\n{'Symbol':<10} {'Price':<12} {'High':<12} {'Low':<12} {'Valid'}")
        print(f"{'─' * 70}")
        for r in results:
            valid_str = '✅' if r['valid'] else '❌'
            print(f"{r['symbol']:<10} ${r['price']:<11.2f} ${r['high']:<11.2f} ${r['low']:<11.2f} {valid_str}")
        
        all_valid = all(r['valid'] for r in results)
        if all_valid:
            print(f"\n✅ All prices are within their daily ranges - DATA IS VALID!")
        else:
            print(f"\n⚠️ Some prices are outside their daily ranges - CHECK DATA!")


async def main():
    """Run all tests"""
    print("\n" + "█" * 70)
    print("🧪 REAL API TEST - STOCK DATA VERIFICATION")
    print("█" * 70)
    print(f"\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Keys Configured:")
    print(f"  Finnhub:       {'✅ Yes' if FINNHUB_TOKEN else '❌ No'}")
    print(f"  Alpha Vantage: {'✅ Yes' if ALPHA_VANTAGE_KEY else '❌ No'}")
    
    # Test Finnhub (primary)
    finnhub_ok = await test_finnhub_api()
    
    # Small delay between API calls
    await asyncio.sleep(2)
    
    # Test Alpha Vantage (fallback)
    alpha_ok = await test_alpha_vantage_api()
    
    # Test multiple symbols
    await asyncio.sleep(2)
    await test_multiple_symbols()
    
    # Show manual verification links
    await compare_with_web()
    
    # Final summary
    print("\n" + "█" * 70)
    print("📋 FINAL VERDICT")
    print("█" * 70)
    
    if finnhub_ok:
        print("\n✅ PRIMARY API (Finnhub): Working correctly")
        print("   └─> Will use this for stock data")
    else:
        print("\n⚠️ PRIMARY API (Finnhub): Not working")
        print("   └─> Check API key or rate limits")
    
    if alpha_ok:
        print("\n✅ FALLBACK API (Alpha Vantage): Working correctly")
        print("   └─> Available as backup")
    elif not finnhub_ok:
        print("\n⚠️ FALLBACK API (Alpha Vantage): Not working")
        print("   └─> Both APIs failed - check keys and network")
    
    if finnhub_ok or alpha_ok:
        print("\n✅ CONCLUSION: Stock service will work!")
        print("   Next: Go to http://127.0.0.1:8000/api/v1/plugins/stocks/")
        print("   and click 'Start Service' to populate the database")
    else:
        print("\n❌ CONCLUSION: Both APIs failed")
        print("   Check:")
        print("   - API keys are correct")
        print("   - Network connection")
        print("   - Rate limits")
    
    print("█" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
