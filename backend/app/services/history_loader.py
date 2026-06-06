# app/services/history_loader.py

from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.models.candles_1m import Candle1m

ALPACA_API_KEY = "PKSQADWO6NSFCZ3XOMK4RG54YA"
ALPACA_SECRET_KEY = "5fJMeiCcTt5XJ2wcNzZAnwTLTn8HbYKLy1yjXEJWWKRo"

client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


def load_history_1m(db: Session, symbol: str, years: int = 3):
    print(f"📥 Loading {years} years of 1m candles for {symbol} using Alpaca SDK...")

    # Clamp end date to today's real date (avoid future timestamps)
    end = datetime.combine(date.today(), datetime.min.time())
    start = end - timedelta(days=365 * years)

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
    return inserted
