"""
API routes for the stocks plugin.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .services import StockService
from .models import Stock, Alert, LatestPrice


class StockCreate(BaseModel):
    """Stock creation model."""
    symbol: str
    target: float
    direction: str  # 'above' or 'below'
    enabled: bool = True


class StockUpdate(BaseModel):
    """Stock update model."""
    target: float = None
    direction: str = None
    enabled: bool = None


def setup_routes(router: APIRouter, stock_service: StockService) -> None:
    """Setup API routes for stocks plugin."""
    
    @router.get("/stocks", response_model=List[Dict[str, Any]])
    async def get_tracked_stocks():
        """Get all tracked stocks."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        stocks_data = db.execute_query("""
            SELECT s.id, s.symbol, s.target, s.direction, s.enabled,
                   p.price, p.high, p.low, p.ts,
                   pr.pred_next
            FROM stocks s
            LEFT JOIN latest_prices p ON s.symbol = p.symbol
            LEFT JOIN predictions pr ON s.symbol = pr.symbol
            ORDER BY s.symbol
        """)
        
        return [dict(row) for row in stocks_data]
    
    @router.post("/stocks", response_model=Dict[str, Any])
    async def create_stock(stock_data: StockCreate):
        """Create a new tracked stock."""
        from ...app_new.core.database import get_database_manager
        
        # Validate direction
        if stock_data.direction not in ['above', 'below']:
            raise HTTPException(status_code=400, detail="Direction must be 'above' or 'below'")
        
        db = get_database_manager()
        
        try:
            stock_id = db.execute_update("""
                INSERT INTO stocks (symbol, target, direction, enabled)
                VALUES (?, ?, ?, ?)
            """, (stock_data.symbol.upper(), stock_data.target, stock_data.direction, stock_data.enabled))
            
            return {
                "id": stock_id,
                "symbol": stock_data.symbol.upper(),
                "target": stock_data.target,
                "direction": stock_data.direction,
                "enabled": stock_data.enabled
            }
        
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=400, detail="Stock symbol already tracked")
            raise HTTPException(status_code=500, detail="Failed to create stock")
    
    @router.put("/stocks/{stock_id}", response_model=Dict[str, Any])
    async def update_stock(stock_id: int, stock_data: StockUpdate):
        """Update a tracked stock."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        
        # Build update query dynamically
        updates = []
        params = []
        
        if stock_data.target is not None:
            updates.append("target = ?")
            params.append(stock_data.target)
        
        if stock_data.direction is not None:
            if stock_data.direction not in ['above', 'below']:
                raise HTTPException(status_code=400, detail="Direction must be 'above' or 'below'")
            updates.append("direction = ?")
            params.append(stock_data.direction)
        
        if stock_data.enabled is not None:
            updates.append("enabled = ?")
            params.append(stock_data.enabled)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(stock_id)
        query = f"UPDATE stocks SET {', '.join(updates)} WHERE id = ?"
        
        affected_rows = db.execute_update(query, tuple(params))
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Get updated stock
        updated_stock = db.execute_query(
            "SELECT * FROM stocks WHERE id = ?", (stock_id,)
        )
        
        if updated_stock:
            return dict(updated_stock[0])
        else:
            raise HTTPException(status_code=404, detail="Stock not found")
    
    @router.delete("/stocks/{stock_id}")
    async def delete_stock(stock_id: int):
        """Delete a tracked stock."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        affected_rows = db.execute_update("DELETE FROM stocks WHERE id = ?", (stock_id,))
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        return {"message": "Stock deleted successfully"}
    
    @router.get("/alerts", response_model=List[Dict[str, Any]])
    async def get_alerts(limit: int = 50):
        """Get recent alerts."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        alerts_data = db.execute_query("""
            SELECT * FROM alerts 
            ORDER BY ts DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in alerts_data]
    
    @router.get("/alerts/recent", response_model=List[Dict[str, Any]])
    async def get_recent_alerts():
        """Get alerts from the last 24 hours."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        alerts_data = db.execute_query("""
            SELECT * FROM alerts 
            WHERE ts >= datetime('now', '-1 day')
            ORDER BY ts DESC
        """)
        
        return [dict(row) for row in alerts_data]
    
    @router.post("/alerts/test")
    async def test_alerts():
        """Test alert system by checking all conditions."""
        alerts = await stock_service.check_alerts()
        return {
            "message": f"Alert check completed, {len(alerts)} alerts triggered",
            "alerts": [alert.to_dict() for alert in alerts]
        }
    
    @router.get("/quotes", response_model=List[Dict[str, Any]])
    async def get_latest_quotes():
        """Get latest quotes for all tracked stocks."""
        from ...app_new.core.database import get_database_manager
        
        db = get_database_manager()
        quotes_data = db.execute_query("""
            SELECT p.symbol, p.price, p.high, p.low, p.ts,
                   pr.pred_next as pred
            FROM latest_prices p
            LEFT JOIN predictions pr ON p.symbol = pr.symbol
            WHERE p.symbol IN (SELECT DISTINCT symbol FROM stocks WHERE enabled = 1)
            ORDER BY p.symbol
        """)
        
        return [dict(row) for row in quotes_data]
    
    @router.get("/showcase", response_model=List[Dict[str, Any]])
    async def get_showcase():
        """Get showcase stocks with latest prices."""
        return await stock_service.get_showcase_data()
    
    @router.post("/quotes/refresh")
    async def refresh_quotes():
        """Manually refresh quotes for all tracked stocks."""
        await stock_service.update_tracked_stocks()
        return {"message": "Quotes refresh initiated"}
    
    @router.get("/quotes/{symbol}", response_model=Dict[str, Any])
    async def get_symbol_quote(symbol: str):
        """Get latest quote for a specific symbol."""
        symbol = symbol.upper()
        price, high, low = await stock_service.fetch_quote(symbol)
        
        if price is None and high is None and low is None:
            raise HTTPException(status_code=404, detail="Quote not found or API error")
        
        return {
            "symbol": symbol,
            "price": price,
            "high": high,
            "low": low
        }
    
    @router.post("/predictions/{symbol}")
    async def update_prediction(symbol: str):
        """Update price prediction for a symbol."""
        symbol = symbol.upper()
        prediction = await stock_service.update_predictions(symbol)
        
        if prediction is None:
            raise HTTPException(status_code=404, detail="Could not generate prediction")
        
        return {
            "symbol": symbol,
            "prediction": prediction
        }
    
    @router.get("/health")
    async def stocks_health():
        """Health check for stocks plugin."""
        connectivity = await stock_service.test_connectivity()
        
        return {
            "plugin": "stocks",
            "status": "healthy",
            "api_connectivity": connectivity
        }