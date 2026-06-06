from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Type

from app.models.candles_1m import Candle1m
# Future models:
# from app.models.candles_5m import Candle5m
# from app.models.candles_1h import Candle1h
# from app.models.candles_1d import Candle1d


# ---------------------------------------------------------
# Timeframe → Model Mapping
# ---------------------------------------------------------
TIMEFRAME_MODEL_MAP = {
    "1m": Candle1m,
    # "5m": Candle5m,
    # "1h": Candle1h,
    # "1d": Candle1d,
}


# ---------------------------------------------------------
# Core Candle Query Function
# ---------------------------------------------------------
def get_candles(
    db: Session,
    symbol: str,
    timeframe: str,
    start_time: datetime,
    end_time: datetime,
):
    """
    Fetch OHLCV candles for a symbol and timeframe between two timestamps.
    """

    # Validate timeframe
    if timeframe not in TIMEFRAME_MODEL_MAP:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    model: Type = TIMEFRAME_MODEL_MAP[timeframe]

    # Query candles
    rows = (
        db.query(model)
        .filter(model.symbol == symbol.upper())
        .filter(model.start_time >= start_time)
        .filter(model.start_time <= end_time)
        .order_by(model.start_time.asc())
        .all()
    )

    return rows
