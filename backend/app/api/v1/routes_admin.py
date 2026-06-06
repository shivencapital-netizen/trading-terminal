from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.history_loader import load_history_1m

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

