from alpaca.trading.client import TradingClient
from app.db.session import SessionLocal
from app.models.instrument import Instrument

ALPACA_API_KEY = "YOUR_KEY"
ALPACA_SECRET_KEY = "YOUR_SECRET"

client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

def load_all_us_stocks():
    assets = client.get_all_assets()

    db = SessionLocal()
    count = 0

    for a in assets:
        if a.tradable and a.status == "active":
            inst = Instrument(
                symbol=a.symbol,
                name=a.name,
                exchange=a.exchange,
                active=True
            )
            db.merge(inst)
            count += 1

    db.commit()
    db.close()

    return count
