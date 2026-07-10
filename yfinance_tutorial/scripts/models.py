"""
Models for scripts


"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StockData:
    name: str
    yf_ticker: str
    # static data
    type: Optional[str] = None
    currency: Optional[str] = None
    market: Optional[str] = None
    isin: Optional[str] = None
    # dynamic: last_time
    last_price: Optional[float] = None

    @classmethod
    def from_dict(cls, name: str, data: dict) -> StockData:
        return cls(name, data[name]["yfTicker"])
