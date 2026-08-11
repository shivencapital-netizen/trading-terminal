import time
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.market_hours import is_regular_market_hours, ny_now
from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.ticks import Tick
from app.models.latest_tick import LatestTick
from app.models.intraday import IntradayCandle

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


# ---------------------------------------------------------
# Alpaca Client
# ---------------------------------------------------------
ALPACA_API_KEY = "PKSQADWO6NSFCZ3XOMK4RG54YA"
ALPACA_SECRET_KEY = "5fJMeiCcTt5XJ2wcNzZAnwTLTn8HbYKLy1yjXEJWWKRo"

client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


# ---------------------------------------------------------
# 1. Tick Ingestion
# ---------------------------------------------------------
def ingest_tick(
    db: Session,
    symbol: str,
    price: float,
    volume: int,
    exchange: str = None
):
    """
    Ingest a single tick into PostgreSQL.
    - Ensures instrument exists
    - Inserts tick into ticks table
    - Updates latest_ticks snapshot table
    """

    instrument = (
        db.query(Instrument)
        .filter(Instrument.symbol == symbol)
        .first()
    )

    if instrument is None:
        print(f"⚠ Unknown symbol received in ticks: {symbol}")
        return None

    tick = Tick(
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=ny_now(),
        exchange=exchange
    )

    db.add(tick)
    db.commit()
    db.refresh(tick)

    latest = (
        db.query(LatestTick)
        .filter(LatestTick.symbol == symbol)
        .first()
    )

    if latest:
        latest.price = price
        latest.volume = volume
        latest.timestamp = ny_now()
    else:
        latest = LatestTick(
            symbol=symbol,
            price=price,
            volume=volume,
            timestamp=ny_now()
        )
        db.add(latest)

    db.commit()
    return tick


# ---------------------------------------------------------
# 2. Get Active Symbols (from instruments table)
# ---------------------------------------------------------
def get_active_symbols():
    db = SessionLocal()
    rows = db.query(Instrument).all()
    db.close()
    return [r.symbol for r in rows]


# ---------------------------------------------------------
# 3. Build 1‑Minute Candle for a Symbol
# ---------------------------------------------------------
def build_intraday_candle(db: Session, symbol: str):
    now = ny_now()
    minute_start = now.replace(second=0, microsecond=0)

    # Get ticks for this minute
    ticks = (
        db.query(Tick)
        .filter(
            Tick.symbol == symbol,
            Tick.timestamp >= minute_start
        )
        .all()
    )

    if not ticks:
        return

    prices = [t.price for t in ticks]
    volumes = [t.volume for t in ticks]

    candle = IntradayCandle(
        symbol=symbol,
        timestamp=minute_start.replace(tzinfo=None),
        open=prices[0],
        high=max(prices),
        low=min(prices),
        close=prices[-1],
        volume=sum(volumes),
        timeframe="1m"
    )

    db.add(candle)
    db.commit()


# ---------------------------------------------------------
# 4. Retention Policy (today only + last 60 candles)
# ---------------------------------------------------------
def cleanup_intraday_retention():
    db = SessionLocal()
    today = ny_now().date()

    db.query(IntradayCandle).filter(
        func.date(IntradayCandle.timestamp) < today
    ).delete(synchronize_session=False)

    symbols = (
        db.query(IntradayCandle.symbol)
        .distinct()
        .all()
    )
    symbols = [s[0] for s in symbols]

    for symbol in symbols:
        subq = (
            db.query(IntradayCandle.id)
            .filter(IntradayCandle.symbol == symbol)
            .order_by(IntradayCandle.timestamp.desc())
            .offset(60)
            .subquery()
        )
        db.query(IntradayCandle).filter(IntradayCandle.id.in_(subq)).delete(
            synchronize_session=False
        )

    db.commit()
    db.close()


# ---------------------------------------------------------
# 5. Candle Builder Loop (runs every minute)
# ---------------------------------------------------------
def candle_builder_loop():
    print("🕒 Candle builder started...")
    waiting_for_market = False

    while True:
        if not is_regular_market_hours():
            if not waiting_for_market:
                print("🕒 Candle builder paused outside regular market hours.")
            waiting_for_market = True
            time.sleep(30)
            continue

        if waiting_for_market:
            print("🕒 Candle builder resumed for regular market hours.")
            waiting_for_market = False

        db = SessionLocal()
        try:
            # Only use symbols YOU inserted
            symbols = get_active_symbols()

            for sym in symbols:
                build_intraday_candle(db, sym)
        finally:
            db.close()

        time.sleep(60)  # run every minute
