import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.core.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, get_alpaca_credentials
from app.core.market_hours import is_regular_market_hours
from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.intraday import IntradayCandle


LIVE_REFRESH_BATCH_SIZE = 50
LIVE_REFRESH_INTERVAL_SECONDS = 60
LIVE_REFRESH_WINDOW_MINUTES = 90


def _get_alpaca_client() -> StockHistoricalDataClient:
    api_key, secret_key = get_alpaca_credentials()
    if not api_key or not secret_key:
        api_key = api_key or ALPACA_API_KEY
        secret_key = secret_key or ALPACA_SECRET_KEY

    if not api_key or not secret_key:
        raise RuntimeError(
            "Alpaca API credentials are not configured. "
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY in your environment or create a .env file."
        )

    return StockHistoricalDataClient(api_key, secret_key)


def _ny_now() -> datetime:
    return datetime.now(ZoneInfo("America/New_York"))


def _market_open_today() -> datetime:
    now = _ny_now()
    return datetime(now.year, now.month, now.day, 9, 30, tzinfo=ZoneInfo("America/New_York"))


def _to_utc(dt: datetime) -> datetime:
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
    return dt.astimezone(ZoneInfo("UTC"))


def _fetch_today_bars(symbol: str, start: datetime, end: datetime):
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=_to_utc(start),
        end=_to_utc(end),
        feed="iex",
    )
    client = _get_alpaca_client()
    bars = client.get_stock_bars(request)
    return bars.df


def _fetch_bars(symbols: list[str], start: datetime, end: datetime):
    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Minute,
        start=_to_utc(start),
        end=_to_utc(end),
        feed="iex",
    )
    client = _get_alpaca_client()
    bars = client.get_stock_bars(request)
    return bars.df


def _chunked(symbols: list[str], size: int):
    for index in range(0, len(symbols), size):
        yield symbols[index:index + size]


def _normalize_intraday_timestamp(ts: datetime) -> datetime:
    if getattr(ts, "tzinfo", None) is None:
        ts = ts.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/New_York"))
    else:
        ts = ts.astimezone(ZoneInfo("America/New_York"))
    return ts.replace(tzinfo=None)


def get_all_symbols(db: Session):
    rows = db.query(Instrument.symbol).order_by(Instrument.symbol).all()
    return [row[0].upper() for row in rows if row and row[0]]


def refresh_live_today_symbol(db: Session, symbol: str) -> int:
    symbol = symbol.upper()
    start = _market_open_today()
    end = _ny_now()

    if start >= end:
        return 0

    # Remove today's existing intraday candles for this symbol before reloading
    db.query(IntradayCandle).filter(
        IntradayCandle.symbol == symbol,
        func.date(IntradayCandle.timestamp) == start.date(),
    ).delete(synchronize_session=False)
    db.commit()

    df = _fetch_today_bars(symbol, start, end)
    if df.empty:
        return 0

    inserted = 0
    for index, row in df.iterrows():
        ts = index[1] if len(index) == 2 else index
        ts = _normalize_intraday_timestamp(ts)

        candle = IntradayCandle(
            symbol=symbol,
            timestamp=ts,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"]),
            timeframe="1m",
        )
        db.add(candle)
        inserted += 1

    db.commit()
    return inserted


def refresh_live_today_all(db: Session):
    symbols = get_all_symbols(db)
    total = 0
    for symbol in symbols:
        total += refresh_live_today_symbol(db, symbol)
    return total


def refresh_live_recent_symbols(
    db: Session,
    symbols: list[str],
    window_minutes: int = LIVE_REFRESH_WINDOW_MINUTES,
    batch_size: int = LIVE_REFRESH_BATCH_SIZE,
) -> int:
    symbols = [symbol.upper() for symbol in symbols if symbol]
    if not symbols:
        return 0

    end = _ny_now()
    start = end - timedelta(minutes=window_minutes)
    start_naive = start.replace(tzinfo=None)
    session_date = end.date()
    inserted = 0

    for chunk in _chunked(symbols, batch_size):
        df = _fetch_bars(chunk, start, end)

        db.query(IntradayCandle).filter(
            IntradayCandle.symbol.in_(chunk),
            func.date(IntradayCandle.timestamp) == session_date,
            IntradayCandle.timestamp >= start_naive,
        ).delete(synchronize_session=False)
        db.commit()

        if df.empty:
            continue

        for index, row in df.iterrows():
            symbol = index[0] if isinstance(index, tuple) else chunk[0]
            ts = index[1] if isinstance(index, tuple) else index
            ts = _normalize_intraday_timestamp(ts)

            db.add(
                IntradayCandle(
                    symbol=str(symbol).upper(),
                    timestamp=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                    timeframe="1m",
                )
            )
            inserted += 1

        db.commit()
        time.sleep(0.25)

    return inserted


def refresh_live_recent_all(db: Session, window_minutes: int = LIVE_REFRESH_WINDOW_MINUTES) -> int:
    return refresh_live_recent_symbols(db, get_all_symbols(db), window_minutes=window_minutes)


def start_live_recent_polling(
    interval_seconds: int = LIVE_REFRESH_INTERVAL_SECONDS,
    window_minutes: int = LIVE_REFRESH_WINDOW_MINUTES,
):
    waiting_for_market = False

    while True:
        if not is_regular_market_hours():
            if not waiting_for_market:
                print("📉 Recent live bar polling paused outside regular market hours.")
            waiting_for_market = True
            time.sleep(30)
            continue

        if waiting_for_market:
            print("📈 Recent live bar polling resumed for regular market hours.")
            waiting_for_market = False

        db = SessionLocal()
        try:
            inserted = refresh_live_recent_all(db, window_minutes=window_minutes)
            print(f"📈 Refreshed recent live bars: {inserted}")
        except Exception as exc:
            print(f"❌ Recent live bar polling error: {exc}")
        finally:
            db.close()

        time.sleep(interval_seconds)
