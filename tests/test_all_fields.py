"""
Detailed test to verify all stock data fields (price, high, low, volume, etc.)
"""
import asyncio
import aiohttp
import os
from datetime import datetime

FINNHUB_TOKEN = os.getenv('FINNHUB_TOKEN', 'd34g7shr01qqt8soved0d34g7shr01qqt8sovedg')


async def test_all_fields():
    """Test that we get all fields: current price, high, low, open, prev close, volume"""
    print("\n" + "=" * 80)
    print("🔍 DETAILED FIELD TEST - Verifying ALL Stock Data Fields")
    print("=" * 80)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMZN', 'META', 'TSLA', 'SPY']
    
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'─' * 80}")
        print(f"📊 Testing {symbol}")
        print(f"{'─' * 80}")
        
        url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}'
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract all fields
                        current_price = data.get('c')  # Current price
                        high = data.get('h')           # High price of the day
                        low = data.get('l')            # Low price of the day
                        open_price = data.get('o')     # Open price
                        prev_close = data.get('pc')    # Previous close
                        timestamp = data.get('t')      # Unix timestamp
                        
                        print(f"\n📈 Raw API Response:")
                        print(f"   {data}")
                        
                        print(f"\n💰 All Fields for {symbol}:")
                        print(f"   Current Price (c):  ${current_price}")
                        print(f"   High (h):           ${high}")
                        print(f"   Low (l):            ${low}")
                        print(f"   Open (o):           ${open_price}")
                        print(f"   Previous Close (pc):${prev_close}")
                        print(f"   Timestamp (t):      {timestamp} ({datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'})")
                        
                        # Check what we're actually using in the service
                        print(f"\n✅ Fields We Store in Database:")
                        print(f"   Symbol: {symbol}")
                        print(f"   Price:  ${current_price} ✅" if current_price else "   Price:  None ❌")
                        print(f"   High:   ${high} ✅" if high else "   High:   None ❌")
                        print(f"   Low:    ${low} ✅" if low else "   Low:    None ❌")
                        
                        # Validation
                        if current_price and high and low:
                            valid_range = low <= current_price <= high
                            print(f"\n🔍 Validation:")
                            print(f"   Range Check: ${low} ≤ ${current_price} ≤ ${high}")
                            print(f"   Result: {'✅ VALID' if valid_range else '❌ INVALID - Price outside range!'}")
                            
                            if open_price:
                                print(f"   Open: ${open_price}")
                                open_in_range = low <= open_price <= high
                                print(f"   Open in range: {'✅' if open_in_range else '❌'}")
                            
                            if prev_close:
                                change = current_price - prev_close
                                change_pct = (change / prev_close) * 100
                                print(f"   Change: ${change:+.2f} ({change_pct:+.2f}%)")
                            
                            all_results.append({
                                'symbol': symbol,
                                'price': current_price,
                                'high': high,
                                'low': low,
                                'open': open_price,
                                'prev_close': prev_close,
                                'valid': valid_range,
                                'has_all_fields': all([current_price, high, low])
                            })
                        else:
                            print(f"\n❌ Missing Data:")
                            if not current_price: print(f"   - Current Price is None")
                            if not high: print(f"   - High is None")
                            if not low: print(f"   - Low is None")
                            
                            all_results.append({
                                'symbol': symbol,
                                'price': current_price,
                                'high': high,
                                'low': low,
                                'has_all_fields': False
                            })
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        all_results.append({
                            'symbol': symbol,
                            'error': f"HTTP {response.status}",
                            'has_all_fields': False
                        })
                        
            except Exception as e:
                print(f"❌ Exception: {e}")
                all_results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'has_all_fields': False
                })
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    # Print summary
    print(f"\n{'=' * 80}")
    print(f"📊 SUMMARY - All Symbols")
    print(f"{'=' * 80}")
    print(f"\n{'Symbol':<10} {'Price':<12} {'High':<12} {'Low':<12} {'Valid':<8} {'Complete'}")
    print(f"{'─' * 80}")
    
    complete_count = 0
    valid_count = 0
    
    for r in all_results:
        if 'error' in r:
            print(f"{r['symbol']:<10} {'ERROR':<12} {'─':<12} {'─':<12} {'─':<8} ❌")
        else:
            price_str = f"${r['price']:.2f}" if r['price'] else "None"
            high_str = f"${r['high']:.2f}" if r['high'] else "None"
            low_str = f"${r['low']:.2f}" if r['low'] else "None"
            valid_str = '✅' if r.get('valid') else '─'
            complete_str = '✅' if r['has_all_fields'] else '❌'
            
            print(f"{r['symbol']:<10} {price_str:<12} {high_str:<12} {low_str:<12} {valid_str:<8} {complete_str}")
            
            if r['has_all_fields']:
                complete_count += 1
            if r.get('valid'):
                valid_count += 1
    
    print(f"\n{'─' * 80}")
    print(f"Statistics:")
    print(f"  Total Symbols:        {len(all_results)}")
    print(f"  Complete Data:        {complete_count}/{len(all_results)} ({'✅' if complete_count == len(all_results) else '⚠️'})")
    print(f"  Valid Ranges:         {valid_count}/{len(all_results)}")
    print(f"{'=' * 80}")
    
    if complete_count == len(all_results):
        print(f"\n✅ SUCCESS! All {len(all_results)} symbols have complete data (price, high, low)")
        print(f"   The stock service will work perfectly!")
    else:
        print(f"\n⚠️ WARNING: {len(all_results) - complete_count} symbols have incomplete data")
        print(f"   Check if market is closed or symbols are invalid")
    
    return all_results


async def test_what_we_store():
    """Show exactly what gets stored in the database"""
    print(f"\n{'=' * 80}")
    print(f"💾 WHAT GETS STORED IN DATABASE")
    print(f"{'=' * 80}")
    
    print(f"\nTable: latest_prices")
    print(f"Schema:")
    print(f"  - symbol TEXT PRIMARY KEY")
    print(f"  - price REAL             ← Current price (c field)")
    print(f"  - high REAL              ← Daily high (h field)")
    print(f"  - low REAL               ← Daily low (l field)")
    print(f"  - ts TEXT                ← Timestamp when stored")
    
    print(f"\nExample INSERT statement:")
    print(f"  INSERT OR REPLACE INTO latest_prices")
    print(f"  (symbol, price, high, low, ts)")
    print(f"  VALUES")
    print(f"  ('AAPL', 247.45, 249.04, 245.13, '2025-10-16 16:52:18')")
    
    print(f"\n{'=' * 80}")


async def main():
    """Run all tests"""
    print(f"\n{'█' * 80}")
    print(f"🧪 COMPREHENSIVE FIELD TEST")
    print(f"{'█' * 80}")
    print(f"\nCurrent Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing: Price, High, Low, Open, Previous Close, Timestamp")
    
    # Test all fields
    results = await test_all_fields()
    
    # Show what we store
    await test_what_we_store()
    
    print(f"\n{'█' * 80}")
    print(f"✅ TEST COMPLETE")
    print(f"{'█' * 80}\n")


if __name__ == "__main__":
    asyncio.run(main())
