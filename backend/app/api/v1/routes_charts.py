from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.schemas.chart import Candle
from app.services.chart_engine import get_candles

router = APIRouter()

@router.get("/{symbol}", response_model=List[Candle])
def read_chart(
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
):
    if timeframe not in ("1m", "5m", "1h", "1d"):
        raise HTTPException(status_code=400, detail="Invalid timeframe")

    candles = get_candles(
        db=db,
        symbol=symbol.upper(),
        timeframe=timeframe,
        start_time=start_time,
        end_time=end_time,
    )
    return candles
