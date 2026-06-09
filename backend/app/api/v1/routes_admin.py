from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

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
def get_all_symbols(db: Session):
    rows = db.query(Instrument.symbol).order_by(Instrument.symbol).all()
    symbols = [row[0] for row in rows if row and row[0]]
    if not symbols:
        raise HTTPException(status_code=404, detail="No symbols found in instruments table.")
    return [symbol.upper() for symbol in symbols]


@router.post("/load-history-1m")
def load_history_1m_api(
    symbol: Optional[str] = None,
    years: int = 1,
    db: Session = Depends(get_db)
):
    """
    Loads multi-year 1-minute OHLCV candles from Alpaca
    and stores them in candles_1m table.
    """
    if symbol:
        inserted = load_history_1m(db, symbol, years)
        return {
            "symbol": symbol.upper(),
            "inserted": inserted
        }

    symbols = get_all_symbols(db)
    total_inserted = 0
    for symbol_name in symbols:
        total_inserted += load_history_1m(db, symbol_name, years)

    return {
        "symbol": "ALL",
        "symbol_count": len(symbols),
        "inserted": total_inserted
    }


# ---------------------------------------------------------
# Load Incremental 1-Minute Candle Delta
# ---------------------------------------------------------
@router.post("/load-history-1m-delta")
def load_history_1m_delta_api(
    symbol: Optional[str] = None,
    years: int = 1,
    db: Session = Depends(get_db)
):
    """
    Loads only new 1-minute bars for a symbol and updates the latest candle snapshot.
    If no previous data exists, the endpoint will backfill the last `years` years.
    """
    if symbol:
        inserted = load_history_1m_delta(db, symbol, years)
        return {
            "symbol": symbol.upper(),
            "inserted": inserted
        }

    symbols = get_all_symbols(db)
    total_inserted = 0
    for symbol_name in symbols:
        total_inserted += load_history_1m_delta(db, symbol_name, years)

    return {
        "symbol": "ALL",
        "symbol_count": len(symbols),
        "inserted": total_inserted
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
        
        last_loaded_time = getattr(instr, "last_loaded_time", None)
        status.append({
            "symbol": instr.symbol,
            "candle_count": candle_count,
            "last_loaded_time": last_loaded_time.isoformat() if last_loaded_time else None,
        })
    
    return status


# ---------------------------------------------------------
# Delete 1-Minute History
# ---------------------------------------------------------
@router.post("/delete-history-1m")
def delete_history_1m_api(
    mode: str = "symbol-year",
    symbol: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Delete historical 1-minute candles according to mode:
    - mode=all: delete all candles
    - mode=all-years: delete all years for a given symbol (requires symbol)
    - mode=current-year: delete current year data for all symbols
    - mode=symbol-year: delete a single symbol for a given year (requires symbol and year)
    Returns number of deleted rows.
    """
    query = db.query(Candle1m)

    if mode == "all":
        deleted = query.delete(synchronize_session=False)

    elif mode == "all-years":
        if not symbol:
            return {"detail": "symbol required for all-years mode"}
        deleted = query.filter(Candle1m.symbol == symbol.upper()).delete(synchronize_session=False)

    elif mode == "current-year":
        from datetime import datetime
        start = datetime(datetime.now().year, 1, 1)
        deleted = query.filter(Candle1m.start_time >= start).delete(synchronize_session=False)

    elif mode == "symbol-year":
        if not symbol or not year:
            return {"detail": "symbol and year required for symbol-year mode"}
        from datetime import datetime
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        deleted = query.filter(
            Candle1m.symbol == symbol.upper(),
            Candle1m.start_time >= start,
            Candle1m.start_time < end,
        ).delete(synchronize_session=False)

    else:
        return {"detail": "unknown mode"}

    # After deletion, update instruments.last_loaded_time for affected symbols
    def _update_for_symbol(sym: Optional[str]):
        if not sym:
            return
        instr = db.query(Instrument).filter(Instrument.symbol == sym.upper()).one_or_none()
        if instr:
            last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == sym.upper()).scalar()
            instr.last_loaded_time = last
            db.add(instr)

    if mode == "all":
        # update all instruments
        instruments = db.query(Instrument).all()
        for instr in instruments:
            last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == instr.symbol).scalar()
            instr.last_loaded_time = last
            db.add(instr)
    elif mode == "current-year":
        # current-year affects all symbols as well
        instruments = db.query(Instrument).all()
        for instr in instruments:
            last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == instr.symbol).scalar()
            instr.last_loaded_time = last
            db.add(instr)
    elif mode in ("all-years", "symbol-year"):
        # affects a single symbol
        _update_for_symbol(symbol)

    db.commit()

    return {"deleted": deleted}

