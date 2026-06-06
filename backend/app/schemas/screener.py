# app/schemas/screener.py

"""
Screener schemas define:
1. What filters the user can send (symbol, price range, volume)
2. What fields we return for each instrument
"""

from pydantic import BaseModel
from typing import Optional


class ScreenerFilters(BaseModel):
    """
    Filters the user can apply when running the screener.
    All fields are optional so the user can send any combination.
    """
    symbol: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_volume: Optional[int] = None


class ScreenerResult(BaseModel):
    """
    Defines what each screener result row looks like.
    ORM mode allows SQLAlchemy models to be returned directly.
    """
    symbol: str
    last_price: float
    volume: int

    class Config:
        orm_mode = True
