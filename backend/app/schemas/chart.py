from datetime import datetime
from pydantic import BaseModel

class Candle(BaseModel):
    start_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    class Config:
        from_attributes = True
