from datetime import datetime
from pydantic import BaseModel


class DelayedQuote(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    delayed_by_minutes: int
    updated_at: datetime
    source: str

    class Config:
        orm_mode = True
