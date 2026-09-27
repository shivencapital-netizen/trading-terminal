import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alpaca.common.exceptions import APIError

from app.core.market_hours import ny_now
from app.db.session import get_db
from app.services.history_loader import (
    load_history_1m,
    load_history_1m_delta,
    load_history_1m_backfill_missing,
)
from app.services.live_loader import refresh_live_today_symbol, refresh_live_today_all
from app.models.instrument import Instrument
from app.models.candles_1m import Candle1m
from app.models.intraday import IntradayCandle
from app.models.symbol_load_summary import SymbolLoadSummary

router = APIRouter()


# ---------------------------------------------------------
# Admin Test Endpoint
# ---------------------------------------------------------
@router.get("/test")
def test_admin():
    return {"message": "Admin router working"}


@router.get("/instruments")
def list_instruments(db: Session = Depends(get_db)):
    instruments = db.query(Instrument).order_by(Instrument.symbol).all()
    return [
        {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "exchange": instrument.exchange,
        }
        for instrument in instruments
    ]


@router.post("/instruments", status_code=201)
def add_instrument(symbol: str, db: Session = Depends(get_db)):
    normalized_symbol = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,14}", normalized_symbol):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid symbol using up to 15 letters, numbers, dots, or hyphens.",
        )

    if db.query(Instrument).filter(Instrument.symbol == normalized_symbol).first():
        raise HTTPException(status_code=409, detail=f"{normalized_symbol} is already in the instrument list.")

    instrument = Instrument(symbol=normalized_symbol)
    db.add(instrument)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"{normalized_symbol} is already in the instrument list.")
    db.refresh(instrument)
    return {
        "symbol": instrument.symbol,
        "name": instrument.name,
        "exchange": instrument.exchange,
    }


@router.delete("/instruments/{symbol}")
def remove_instrument(symbol: str, db: Session = Depends(get_db)):
    normalized_symbol = symbol.strip().upper()
    instrument = db.query(Instrument).filter(Instrument.symbol == normalized_symbol).one_or_none()
    if instrument is None:
        raise HTTPException(status_code=404, detail=f"{normalized_symbol} was not found in the instrument list.")

    db.delete(instrument)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This instrument is referenced by existing records and cannot be removed.",
        )
    return {"symbol": normalized_symbol, "removed": True}


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
def get_never_loaded_symbols(db: Session):
    rows = (
        db.query(Instrument.symbol)
        .filter(Instrument.last_loaded_time.is_(None))
        .order_by(Instrument.symbol)
        .all()
    )
    return [row[0] for row in rows if row and row[0]]


@router.post("/load-history-1m-delta")
def load_history_1m_delta_api(
    symbol: Optional[str] = None,
    years: int = 1,
    mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Loads only new 1-minute bars for a symbol and updates the latest candle snapshot.
    If no previous data exists, the endpoint will backfill the last `years` years.
    """
    if symbol and mode == "backfill-missing":
        inserted = load_history_1m_backfill_missing(db, symbol, years)
        return {
            "symbol": symbol.upper(),
            "inserted": inserted,
            "mode": "backfill-missing",
            "years": years,
        }

    if symbol:
        inserted = load_history_1m_delta(db, symbol, years)
        return {
            "symbol": symbol.upper(),
            "inserted": inserted
        }

    if mode == "never":
        symbols = get_never_loaded_symbols(db)
        total_inserted = 0
        for symbol_name in symbols:
            total_inserted += load_history_1m_delta(db, symbol_name, years)

        return {
            "symbol": "NEVER",
            "symbol_count": len(symbols),
            "inserted": total_inserted
        }

    if mode == "backfill-missing":
        symbols = get_all_symbols(db)
        total_inserted = 0
        for symbol_name in symbols:
            total_inserted += load_history_1m_backfill_missing(db, symbol_name, years)

        return {
            "symbol": "ALL",
            "symbol_count": len(symbols),
            "inserted": total_inserted,
            "mode": "backfill-missing",
            "years": years,
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


@router.post("/refresh-live-today")
def refresh_live_today_api(
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Refresh today's intraday candles from market open (9:30 ET) to now.
    Does not affect historical candles in candles_1m for previous days.
    """
    try:
        if symbol:
            inserted = refresh_live_today_symbol(db, symbol)
            return {
                "symbol": symbol.upper(),
                "inserted": inserted,
            }

        inserted = refresh_live_today_all(db)
        return {
            "symbol": "ALL",
            "symbol_count": len(get_all_symbols(db)),
            "inserted": inserted,
        }
    except APIError as ex:
        message = None
        try:
            message = ex.message
        except Exception:
            message = str(ex)

        status_code = getattr(ex, "status_code", None)
        if status_code == 401:
            message = (
                f"{message} (check ALPACA_API_KEY and ALPACA_SECRET_KEY in backend env or .env)"
            )
        if not message:
            message = "Unknown Alpaca API error"
        raise HTTPException(status_code=502, detail=f"Alpaca API error: {message}")
    except RuntimeError as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(ex)}")


# ---------------------------------------------------------
# Get Symbol Load Status
# ---------------------------------------------------------
@router.get("/symbol-status")
def get_symbol_status(db: Session = Depends(get_db)):
    """
    Retrieve the load status for all instruments using the fast summary table:
    - Symbol name
    - Candle count from symbol_load_summary
    - Last loaded time from summary or instruments table
    - Start and end candle periods from candles_1m
    """
    candle_range = (
        db.query(
            Candle1m.symbol.label("symbol"),
            func.min(Candle1m.start_time).label("start_period"),
            func.max(Candle1m.start_time).label("end_period"),
        )
        .group_by(Candle1m.symbol)
        .subquery()
    )

    rows = (
        db.query(
            Instrument.symbol,
            Instrument.last_loaded_time,
            SymbolLoadSummary.candle_count,
            SymbolLoadSummary.last_loaded_time.label("summary_last_loaded_time"),
            candle_range.c.start_period,
            candle_range.c.end_period,
        )
        .outerjoin(SymbolLoadSummary, SymbolLoadSummary.symbol == Instrument.symbol)
        .outerjoin(candle_range, candle_range.c.symbol == Instrument.symbol)
        .order_by(Instrument.symbol)
        .all()
    )

    status = []
    for symbol, instrument_last_loaded_time, candle_count, summary_last_loaded_time, start_period, end_period in rows:
        last_loaded_time = summary_last_loaded_time or instrument_last_loaded_time
        status.append({
            "symbol": symbol,
            "candle_count": candle_count or 0,
            "last_loaded_time": last_loaded_time.isoformat() if last_loaded_time else None,
            "start_period": start_period.isoformat() if start_period else None,
            "end_period": end_period.isoformat() if end_period else None,
        })

    return status


@router.get("/latest-live-candles")
def get_latest_live_candles(
    symbol: Optional[str] = None,
    limit: int = 600,
    db: Session = Depends(get_db),
):
    """
    Return the latest intraday candle by symbol for today's SP500/SPY universe.
    Universe is based on the instruments table loaded in this project.
    """
    now = ny_now().replace(tzinfo=None)
    today = now.date()

    latest_per_symbol = (
        db.query(
            IntradayCandle.symbol.label("symbol"),
            func.max(IntradayCandle.timestamp).label("latest_ts"),
        )
        .filter(
            func.date(IntradayCandle.timestamp) == today,
            IntradayCandle.timestamp <= now,
        )
        .group_by(IntradayCandle.symbol)
        .subquery()
    )

    query = (
        db.query(
            IntradayCandle.symbol,
            IntradayCandle.timestamp,
            IntradayCandle.open,
            IntradayCandle.high,
            IntradayCandle.low,
            IntradayCandle.close,
            IntradayCandle.volume,
        )
        .join(
            latest_per_symbol,
            (IntradayCandle.symbol == latest_per_symbol.c.symbol)
            & (IntradayCandle.timestamp == latest_per_symbol.c.latest_ts),
        )
        .join(Instrument, Instrument.symbol == IntradayCandle.symbol)
        .order_by(IntradayCandle.symbol)
    )

    if symbol:
        query = query.filter(IntradayCandle.symbol.ilike(f"%{symbol.upper()}%"))

    rows = query.limit(max(1, min(limit, 2000))).all()

    return [
        {
            "symbol": row.symbol,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": int(row.volume),
        }
        for row in rows
    ]


# ---------------------------------------------------------
# Delete 1-Minute History
# ---------------------------------------------------------
@router.post("/delete-history-1m")
def delete_history_1m_api(
    mode: str = "symbol-year",
    symbol: Optional[str] = None,
    year: Optional[int] = None,
    before_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Delete historical 1-minute candles according to mode:
    - mode=all: delete all candles
    - mode=all-years: delete all years for a given symbol (requires symbol)
    - mode=current-year: delete current year data for all symbols
    - mode=symbol-year: delete a single symbol for a given year (requires symbol and year)
    - mode=before-date: delete all symbols' data with start_time before the given date (requires before_date, format YYYY-MM-DD)
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

    elif mode == "before-date":
        if not before_date:
            return {"detail": "before_date required for before-date mode"}
        from datetime import datetime
        try:
            cutoff = datetime.strptime(before_date, "%Y-%m-%d")
        except ValueError:
            return {"detail": "before_date must be in YYYY-MM-DD format"}
        deleted = query.filter(Candle1m.start_time < cutoff).delete(synchronize_session=False)

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

    if mode in ("all", "before-date"):
        # update all instruments and summary rows
        instruments = db.query(Instrument).all()
        for instr in instruments:
            last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == instr.symbol).scalar()
            instr.last_loaded_time = last
            db.add(instr)
            summary = db.query(SymbolLoadSummary).filter(SymbolLoadSummary.symbol == instr.symbol).one_or_none()
            if summary:
                summary.candle_count = db.query(func.count(Candle1m.id)).filter(Candle1m.symbol == instr.symbol).scalar() or 0
                summary.last_loaded_time = last
                summary.updated_at = func.now()
            else:
                db.add(SymbolLoadSummary(symbol=instr.symbol, candle_count=0, last_loaded_time=last))
    elif mode == "current-year":
        # current-year affects all symbols as well
        instruments = db.query(Instrument).all()
        for instr in instruments:
            last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == instr.symbol).scalar()
            instr.last_loaded_time = last
            db.add(instr)
            summary = db.query(SymbolLoadSummary).filter(SymbolLoadSummary.symbol == instr.symbol).one_or_none()
            if summary:
                summary.candle_count = db.query(func.count(Candle1m.id)).filter(Candle1m.symbol == instr.symbol).scalar() or 0
                summary.last_loaded_time = last
                summary.updated_at = func.now()
            else:
                db.add(SymbolLoadSummary(symbol=instr.symbol, candle_count=0, last_loaded_time=last))
    elif mode in ("all-years", "symbol-year"):
        # affects a single symbol
        _update_for_symbol(symbol)
        summary = db.query(SymbolLoadSummary).filter(SymbolLoadSummary.symbol == symbol.upper()).one_or_none()
        candle_count = db.query(func.count(Candle1m.id)).filter(Candle1m.symbol == symbol.upper()).scalar() or 0
        last = db.query(func.max(Candle1m.start_time)).filter(Candle1m.symbol == symbol.upper()).scalar()
        if summary:
            summary.candle_count = candle_count
            summary.last_loaded_time = last
            summary.updated_at = func.now()
        else:
            db.add(SymbolLoadSummary(symbol=symbol.upper(), candle_count=candle_count, last_loaded_time=last))

    db.commit()

    return {"deleted": deleted}
