import time
from threading import Thread
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.symbol_load_summary import SymbolLoadSummary
from app.services.history_loader import refresh_symbol_load_summary


def get_symbols_missing_summary(db: Session) -> List[str]:
    rows = (
        db.query(Instrument.symbol)
        .outerjoin(SymbolLoadSummary, SymbolLoadSummary.symbol == Instrument.symbol)
        .filter(SymbolLoadSummary.symbol.is_(None))
        .order_by(Instrument.symbol)
        .all()
    )
    return [row[0] for row in rows if row and row[0]]


def get_symbols_with_stale_summary(db: Session, limit: int = 100) -> List[str]:
    rows = (
        db.query(Instrument.symbol)
        .join(SymbolLoadSummary, SymbolLoadSummary.symbol == Instrument.symbol)
        .filter(
            (Instrument.last_loaded_time.isnot(None) & (Instrument.last_loaded_time != SymbolLoadSummary.last_loaded_time))
            | (Instrument.last_loaded_time.is_(None) & SymbolLoadSummary.last_loaded_time.isnot(None))
        )
        .order_by(Instrument.symbol)
        .limit(limit)
        .all()
    )
    return [row[0] for row in rows if row and row[0]]


def refresh_symbol_load_summaries(limit: int = 100):
    db = SessionLocal()
    try:
        symbols_to_refresh = get_symbols_missing_summary(db)
        symbols_to_refresh += get_symbols_with_stale_summary(db, limit=limit)
        symbols_to_refresh = sorted(set(symbols_to_refresh))

        if not symbols_to_refresh:
            print("🔄 Symbol load summary refresher found no missing or stale rows.")
            return

        print(f"🔄 Refreshing symbol load summary for {len(symbols_to_refresh)} symbols...")
        for symbol in symbols_to_refresh:
            symbol_db = SessionLocal()
            try:
                refresh_symbol_load_summary(symbol_db, symbol)
            except Exception as exc:
                symbol_db.rollback()
                print(f"⚠ Failed to refresh summary for {symbol}: {exc}")
            finally:
                symbol_db.close()
    finally:
        db.close()


def start_symbol_load_summary_refresher(interval_seconds: int = 900):
    def refresh_loop():
        while True:
            try:
                refresh_symbol_load_summaries()
            except Exception as exc:
                print(f"⚠ Symbol load summary refresher error: {exc}")
            time.sleep(interval_seconds)

    thread = Thread(target=refresh_loop, daemon=True)
    thread.start()
    print(f"⏱️ Symbol load summary refresher started; interval={interval_seconds}s")
