# app/services/history_loader.py

from datetime import datetime, timedelta, date
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.models.candles_1m import Candle1m
from app.models.instrument import Instrument
from app.models.latest_candle_1m import LatestCandle1m

ALPACA_API_KEY = "PKSQADWO6NSFCZ3XOMK4RG54YA"
ALPACA_SECRET_KEY = "5fJMeiCcTt5XJ2wcNzZAnwTLTn8HbYKLy1yjXEJWWKRo"

client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


def load_history_1m(
    db: Session,
    symbol: str,
    years: int = 3,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    if end is None:
        end = datetime.combine(date.today(), datetime.min.time())

    if start is None:
        start = end - timedelta(days=365 * years)

    if start >= end:
        raise ValueError("start must be before end")

    print(
        f"📥 Loading 1m candles for {symbol} from {start.isoformat()} to {end.isoformat()} using Alpaca SDK..."
    )

    request_params = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Minute,
        start=start,
        end=end,
        feed="iex"  # REQUIRED for free tier
    )

    bars = client.get_stock_bars(request_params)
    df = bars.df

    if df.empty:
        print(f"⚠ No historical data returned for {symbol}")
        return 0

    inserted = 0

    for index, row in df.iterrows():
        # Extract timestamp from MultiIndex (symbol, timestamp)
        ts = row.name[1]

        # Convert pandas Timestamp → Python datetime
        ts = ts.to_pydatetime()

        # Strip timezone (Postgres requires naive timestamps)
        ts = ts.replace(tzinfo=None)

        candle = Candle1m(
            symbol=symbol,
            start_time=ts,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=int(row["volume"]),
        )

        # Skip duplicates
        exists = (
            db.query(Candle1m)
            .filter(Candle1m.symbol == symbol)
            .filter(Candle1m.start_time == ts)
            .first()
        )

        if exists:
            continue

        db.add(candle)
        inserted += 1

    db.commit()
    print(f"✅ Inserted {inserted} candles for {symbol}")
    update_instrument_last_loaded_time(db, symbol)
    return inserted


def get_latest_candle_time(db: Session, symbol: str) -> Optional[datetime]:
    symbol = symbol.upper()
    latest_time = (
        db.query(func.max(Candle1m.start_time))
        .filter(Candle1m.symbol == symbol)
        .scalar()
    )
    return latest_time


def update_instrument_last_loaded_time(db: Session, symbol: str):
    symbol = symbol.upper()
    latest_time = get_latest_candle_time(db, symbol)
    if latest_time is None:
        return

    instrument = (
        db.query(Instrument)
        .filter(Instrument.symbol == symbol)
        .first()
    )
    if instrument is None:
        return

    instrument.last_loaded_time = latest_time
    db.commit()


def update_latest_candle_snapshot(db: Session, symbol: str):
    symbol = symbol.upper()
    latest = (
        db.query(Candle1m)
        .filter(Candle1m.symbol == symbol)
        .order_by(Candle1m.start_time.desc())
        .first()
    )

    if not latest:
        return

    snapshot = (
        db.query(LatestCandle1m)
        .filter(LatestCandle1m.symbol == symbol)
        .first()
    )

    if snapshot:
        snapshot.start_time = latest.start_time
        snapshot.open = latest.open
        snapshot.high = latest.high
        snapshot.low = latest.low
        snapshot.close = latest.close
        snapshot.volume = latest.volume
        snapshot.updated_at = datetime.utcnow()
    else:
        snapshot = LatestCandle1m(
            symbol=symbol,
            start_time=latest.start_time,
            open=latest.open,
            high=latest.high,
            low=latest.low,
            close=latest.close,
            volume=latest.volume,
            updated_at=datetime.utcnow(),
        )
        db.add(snapshot)

    db.commit()


def load_history_1m_delta(
    db: Session,
    symbol: str,
    years: int = 1,
    delay_minutes: int = 15,
    end: Optional[datetime] = None,
):
    symbol = symbol.upper()

    if end is None:
        end = datetime.utcnow() - timedelta(minutes=delay_minutes)

    latest_time = get_latest_candle_time(db, symbol)
    if latest_time:
        start = latest_time + timedelta(minutes=1)
        print(
            f"🔁 Loading delta 1m candles for {symbol} from {start.isoformat()} to {end.isoformat()}"
        )
    else:
        start = end - timedelta(days=365 * years)
        print(
            f"📥 No existing candles for {symbol}; loading last {years} year(s) from {start.isoformat()} to {end.isoformat()}"
        )

    if start >= end:
        print(f"✅ No new data to load for {symbol}, latest available candle is up to date.")
        return 0

    inserted = load_history_1m(db, symbol, start=start, end=end)
    if inserted:
        update_latest_candle_snapshot(db, symbol)
    return inserted
