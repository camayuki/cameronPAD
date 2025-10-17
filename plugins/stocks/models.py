"""
Stock data models for the stocks plugin.
"""
from typing import Optional
from datetime import datetime


class Stock:
    """Stock tracking model."""
    
    def __init__(self, symbol: str, target: float, direction: str, enabled: bool = True):
        self.symbol = symbol.upper()
        self.target = target
        self.direction = direction  # 'above' or 'below'
        self.enabled = enabled
        self.id: Optional[int] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Create Stock instance from database row."""
        stock = cls(
            symbol=row['symbol'],
            target=row['target'],
            direction=row['direction'],
            enabled=bool(row['enabled'])
        )
        stock.id = row['id']
        return stock
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'target': self.target,
            'direction': self.direction,
            'enabled': self.enabled
        }


class Alert:
    """Stock alert model."""
    
    def __init__(self, symbol: str, price: float, target: float, direction: str):
        self.symbol = symbol.upper()
        self.price = price
        self.target = target
        self.direction = direction
        self.timestamp: Optional[datetime] = None
        self.id: Optional[int] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Create Alert instance from database row."""
        alert = cls(
            symbol=row['symbol'],
            price=row['price'],
            target=row['target'],
            direction=row['direction']
        )
        alert.id = row['id']
        alert.timestamp = datetime.fromisoformat(row['ts']) if row['ts'] else None
        return alert
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'target': self.target,
            'direction': self.direction,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class LatestPrice:
    """Latest stock price model."""
    
    def __init__(self, symbol: str, price: Optional[float] = None, 
                 high: Optional[float] = None, low: Optional[float] = None):
        self.symbol = symbol.upper()
        self.price = price
        self.high = high
        self.low = low
        self.timestamp: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Create LatestPrice instance from database row."""
        price = cls(
            symbol=row['symbol'],
            price=row['price'],
            high=row['high'],
            low=row['low']
        )
        price.timestamp = datetime.fromisoformat(row['ts']) if row['ts'] else None
        return price
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'high': self.high,
            'low': self.low,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Prediction:
    """Stock price prediction model."""
    
    def __init__(self, symbol: str, predicted_next: float, source_days: int):
        self.symbol = symbol.upper()
        self.predicted_next = predicted_next
        self.source_days = source_days
        self.timestamp: Optional[datetime] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Create Prediction instance from database row."""
        prediction = cls(
            symbol=row['symbol'],
            predicted_next=row['pred_next'],
            source_days=row['src_days']
        )
        prediction.timestamp = datetime.fromisoformat(row['ts']) if row['ts'] else None
        return prediction
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'predicted_next': self.predicted_next,
            'source_days': self.source_days,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }