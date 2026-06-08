from app.db.session import SessionLocal
from app.models.instrument import Instrument


def load_sp500():
    db = SessionLocal()
    try:
        symbols = db.query(Instrument.symbol).order_by(Instrument.symbol).all()
        count = len(symbols)
        print(f">>> Loaded {count} symbols from instruments table")
        return count
    finally:
        db.close()
