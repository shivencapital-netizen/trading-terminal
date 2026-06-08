from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.services.history_loader import load_history_1m, load_history_1m_delta
from app.models.instrument import Instrument
from app.models.candles_1m import Candle1m

router = APIRouter()


# ---------------------------------------------------------
# Admin Test Endpoint
# ---------------------------------------------------------
@router.get("/test")
def test_admin():
    return {"message": "Admin router working"}


# ---------------------------------------------------------
# Load Historical 1-Minute Candles (Alpaca)
# ---------------------------------------------------------
@router.post("/load-history-1m")
def load_history_1m_api(
    symbol: str,
    years: int = 1,
    db: Session = Depends(get_db)
):
    """
    Loads multi-year 1-minute OHLCV candles from Alpaca
    and stores them in candles_1m table.
    """
    inserted = load_history_1m(db, symbol, years)
    return {
        "symbol": symbol,
        "inserted": inserted
    }


# ---------------------------------------------------------
# Load Incremental 1-Minute Candle Delta
# ---------------------------------------------------------
@router.post("/load-history-1m-delta")
def load_history_1m_delta_api(
    symbol: str,
    years: int = 1,
    db: Session = Depends(get_db)
):
    """
    Loads only new 1-minute bars for a symbol and updates the latest candle snapshot.
    If no previous data exists, the endpoint will backfill the last `years` years.
    """
    inserted = load_history_1m_delta(db, symbol, years)
    return {
        "symbol": symbol,
        "inserted": inserted
    }
    return {
        "symbol": symbol,
        "inserted": inserted
    }


# ---------------------------------------------------------
# Get Symbol Load Status
# ---------------------------------------------------------
@router.get("/symbol-status")
def get_symbol_status(db: Session = Depends(get_db)):
    """
    Retrieve the load status for all instruments:
    - Symbol name
    - Candle count in candles_1m
    - Last loaded time from instruments table
    """
    instruments = db.query(Instrument).all()
    
    status = []
    for instr in instruments:
        candle_count = (
            db.query(func.count(Candle1m.id))
            .filter(Candle1m.symbol == instr.symbol.upper())
            .scalar() or 0
        )
        
        status.append({
            "symbol": instr.symbol,
            "candle_count": candle_count,
            "last_loaded_time": instr.last_loaded_time.isoformat() if instr.last_loaded_time else None,
        })
    
    return status

