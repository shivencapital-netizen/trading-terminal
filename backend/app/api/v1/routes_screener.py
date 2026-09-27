# app/api/v1/routes_screener.py

"""
Screener API routes.
Provides a GET endpoint that returns computed screener metrics.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.screener import ScreenerFilters
from app.services.screener_engine import run_screener, run_history_screener, run_breakout_screener
from app.services.ma_screener import (
    run_ma_crossover_screener,
    clear_ma_crossover_cache,
    refresh_ma_crossover_cache,
    get_ma_crossover_cache,
)
from app.services.rsi_screener import (
    run_rsi_crossover_screener,
    clear_rsi_crossover_cache,
    refresh_rsi_crossover_cache,
    get_rsi_crossover_cache,
)
from app.services.ath_screener import (
    run_ath_screener,
    clear_ath_screener_cache,
    refresh_ath_screener_cache,
    get_ath_screener_cache,
)

router = APIRouter()


@router.get("/run")
def run_screener_endpoint(
    filters: ScreenerFilters = Depends(),
    symbols: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns computed screener metrics for all symbols that have:
    - a latest tick
    - intraday candles for today
    """
    results = run_screener(db, filters=filters, symbols=symbols)
    return results


@router.get("/history")
def run_history_screener_endpoint(
    filters: ScreenerFilters = Depends(),
    symbols: Optional[list[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Returns screener metrics based on historical candles in candles_1m.
    """
    results = run_history_screener(db, filters=filters, symbols=symbols)
    return results


@router.get("/breakouts")
def run_breakout_screener_endpoint(
    lookback_days: int = 5,
    db: Session = Depends(get_db),
):
    """
    Separate breakout scan: symbols currently trading above prior N-day high.
    Independent from normal filter criteria.
    """
    results = run_breakout_screener(db, lookback_days=lookback_days)
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


@router.get("/rsi-cross")
def run_rsi_crossover_endpoint(
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Return symbols where RSI crossed a threshold on the latest trading day.
    Example: rsi_period=14, rsi_level=59, direction=above
    """
    try:
        return run_rsi_crossover_screener(
            db,
            rsi_period=rsi_period,
            rsi_level=rsi_level,
            direction=direction,
            symbol_contains=symbol_contains,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/rsi-cross/cache/refresh")
def refresh_rsi_crossover_cache_endpoint(
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return refresh_rsi_crossover_cache(
            db,
            rsi_period=rsi_period,
            rsi_level=rsi_level,
            direction=direction,
            symbol_contains=symbol_contains,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/rsi-cross/cache/clear")
def clear_rsi_crossover_cache_endpoint(
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return clear_rsi_crossover_cache(
            db,
            rsi_period=rsi_period,
            rsi_level=rsi_level,
            direction=direction,
            symbol_contains=symbol_contains,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/rsi-cross/cache")
def get_rsi_crossover_cache_endpoint(
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return get_rsi_crossover_cache(
            db,
            rsi_period=rsi_period,
            rsi_level=rsi_level,
            direction=direction,
            symbol_contains=symbol_contains,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/ath-cross")
def run_ath_screener_endpoint(
    direction: str = "above",
    symbol_contains: str | None = None,
    min_history_days: int = 30,
    db: Session = Depends(get_db),
):
    try:
        return run_ath_screener(
            db,
            direction=direction,
            symbol_contains=symbol_contains,
            min_history_days=min_history_days,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/ath-cross/cache/refresh")
def refresh_ath_screener_cache_endpoint(
    direction: str = "above",
    symbol_contains: str | None = None,
    min_history_days: int = 30,
    db: Session = Depends(get_db),
):
    try:
        return refresh_ath_screener_cache(
            db,
            direction=direction,
            symbol_contains=symbol_contains,
            min_history_days=min_history_days,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/ath-cross/cache/clear")
def clear_ath_screener_cache_endpoint(
    direction: str = "above",
    symbol_contains: str | None = None,
    min_history_days: int = 30,
    db: Session = Depends(get_db),
):
    try:
        return clear_ath_screener_cache(
            db,
            direction=direction,
            symbol_contains=symbol_contains,
            min_history_days=min_history_days,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/ath-cross/cache")
def get_ath_screener_cache_endpoint(
    direction: str = "above",
    symbol_contains: str | None = None,
    min_history_days: int = 30,
    db: Session = Depends(get_db),
):
    try:
        return get_ath_screener_cache(
            db,
            direction=direction,
            symbol_contains=symbol_contains,
            min_history_days=min_history_days,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/test")
def test_screener():
    """
    Simple test endpoint to verify router is working.
    """
    return {"message": "Screener router working"}
