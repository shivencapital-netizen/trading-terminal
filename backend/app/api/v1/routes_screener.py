# app/api/v1/routes_screener.py

"""
Screener API routes.
Provides a GET endpoint that returns computed screener metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.screener import ScreenerFilters
from app.services.screener_engine import run_screener, run_history_screener

router = APIRouter()


@router.get("/run")
def run_screener_endpoint(db: Session = Depends(get_db)):
    """
    Returns computed screener metrics for all symbols that have:
    - a latest tick
    - intraday candles for today
    """
    results = run_screener(db)
    return results


@router.get("/history")
def run_history_screener_endpoint(
    filters: ScreenerFilters = Depends(),
    db: Session = Depends(get_db),
):
    """
    Returns screener metrics based on historical candles in candles_1m.
    """
    results = run_history_screener(db, filters=filters)
    return results


@router.get("/test")
def test_screener():
    """
    Simple test endpoint to verify router is working.
    """
    return {"message": "Screener router working"}
