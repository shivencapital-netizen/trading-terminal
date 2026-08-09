# app/api/v1/routes_screener.py

"""
Screener API routes.
Provides a GET endpoint that returns computed screener metrics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.screener import ScreenerFilters
from app.services.screener_engine import run_screener, run_history_screener
from app.services.ma_screener import (
    run_ma_crossover_screener,
    clear_ma_crossover_cache,
    refresh_ma_crossover_cache,
    get_ma_crossover_cache,
)

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


@router.get("/ma-cross")
def run_ma_crossover_endpoint(
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Return symbols where fast MA crossed slow MA on the latest trading day.
    Example: fast_period=10, fast_ma=EMA, slow_period=50, slow_ma=EMA, direction=above
    """
    try:
        return run_ma_crossover_screener(
            db,
            fast_period=fast_period,
            slow_period=slow_period,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            direction=direction,
            symbol_contains=symbol_contains,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/ma-cross/cache/refresh")
def refresh_ma_crossover_cache_endpoint(
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: str | None = None,
    ma_family: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return refresh_ma_crossover_cache(
            db,
            fast_period=fast_period,
            slow_period=slow_period,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            direction=direction,
            symbol_contains=symbol_contains,
            ma_family=ma_family,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/ma-cross/cache/clear")
def clear_ma_crossover_cache_endpoint(
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: str | None = None,
    ma_family: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return clear_ma_crossover_cache(
            db,
            fast_period=fast_period,
            slow_period=slow_period,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            direction=direction,
            symbol_contains=symbol_contains,
            ma_family=ma_family,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/ma-cross/cache")
def get_ma_crossover_cache_endpoint(
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: str | None = None,
    ma_family: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return get_ma_crossover_cache(
            db,
            fast_period=fast_period,
            slow_period=slow_period,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            direction=direction,
            symbol_contains=symbol_contains,
            ma_family=ma_family,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/test")
def test_screener():
    """
    Simple test endpoint to verify router is working.
    """
    return {"message": "Screener router working"}
