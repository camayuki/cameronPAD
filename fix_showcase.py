#!/usr/bin/env python3
"""Fix the showcase endpoint to use get_showcase_data() service method"""

def fix_endpoint():
    filepath = "plugins/stocks/plugin.py"
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start and end of the get_showcase function
    start_marker = '        @self._router.get("/showcase")'
    
    # Find where it starts
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("❌ Could not find showcase endpoint")
        return False
    
    # Find the end - look for the next @self._router or the end of routes
    # The function ends with the return statement and closing brace
    search_from = start_idx + len(start_marker)
    end_marker = '\n        @self._router.'
    end_idx = content.find(end_marker, search_from)
    
    if end_idx == -1:
        # Maybe it's the last route, look for logger.info("✅ Stocks routes registered")
        end_marker = '\n        logger.info("✅ Stocks routes registered")'
        end_idx = content.find(end_marker, search_from)
    
    if end_idx == -1:
        print("❌ Could not find end of function")
        return False
    
    # Extract and replace
    old_function = content[start_idx:end_idx]
    
    new_function = '''        @self._router.get("/showcase")
        async def get_showcase():
            """Get showcase stock quotes from database"""
            logger.info("🌐 [ENDPOINT] /showcase called by frontend")
            quotes = []
            
            try:
                # Use the stock_service method which already handles showcase data correctly
                logger.info("🔍 [ENDPOINT] Calling stock_service.get_showcase_data()...")
                quotes = await self.stock_service.get_showcase_data()
                logger.info(f"✅ [ENDPOINT] Retrieved {len(quotes)} showcase quotes")
                
                # Log each quote for debugging
                for quote in quotes:
                    has_price = quote.get('price') is not None
                    status = "✅ HAS DATA" if has_price else "❌ NO DATA"
                    logger.info(f"📈 [ENDPOINT] {quote['symbol']}: {status} | Price=${quote.get('price', '--')}")
                    
            except Exception as e:
                logger.error(f"❌ [ENDPOINT] Error fetching showcase quotes: {e}", exc_info=True)
            
            logger.info(f"📤 [ENDPOINT] Sending {len(quotes)} quotes to frontend")
            return {
                "status": "success",
                "quotes": quotes
            }
'''
    
    new_content = content[:start_idx] + new_function + content[end_idx:]
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Successfully updated {filepath}")
    print(f"📝 Old function was {len(old_function)} chars")
    print(f"📝 New function is {len(new_function)} chars")
    return True

if __name__ == '__main__':
    fix_endpoint()
