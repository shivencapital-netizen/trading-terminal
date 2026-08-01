from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import GreeksSnapshot
from app.models.instrument import Instrument

router = APIRouter()


@router.get("/test")
def test_greeks():
    return {"message": "Greeks router working"}


@router.get("/latest")
def latest_greeks(symbol: str, db: Session = Depends(get_db)):
    """
    Return the latest GreeksSnapshot for a given instrument symbol.
    Response keys: `implied_vol` (float, as decimal e.g. 0.271), `underlying_price`, `snapshot_at`.
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol query parameter is required")

    sym = symbol.upper()
    instr = db.query(Instrument).filter(Instrument.symbol == sym).first()
    if not instr:
        raise HTTPException(status_code=404, detail=f"Instrument {sym} not found")

    snap = (
        db.query(GreeksSnapshot)
        .filter(GreeksSnapshot.instrument_id == instr.id)
        .order_by(GreeksSnapshot.snapshot_at.desc())
        .first()
    )

    if not snap:
        raise HTTPException(status_code=404, detail=f"No greeks snapshot found for {sym}")

    return {
        "implied_vol": snap.implied_vol,
        "underlying_price": snap.underlying_price,
        "snapshot_at": snap.snapshot_at.isoformat() if snap.snapshot_at else None,
    }
