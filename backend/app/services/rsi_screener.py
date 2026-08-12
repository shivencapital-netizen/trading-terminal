from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m
from app.models.rsi_signal_cache import RSISignalCache


DIRECTIONS = {"above", "below"}


def _get_daily_closes_desc(db: Session, symbol: str, limit_days: int) -> List[float]:
    day_subquery = (
        db.query(
            func.date(Candle1m.start_time).label("candle_day"),
            func.max(Candle1m.start_time).label("last_ts"),
        )
        .filter(Candle1m.symbol == symbol)
        .group_by(func.date(Candle1m.start_time))
        .order_by(func.date(Candle1m.start_time).desc())
        .limit(limit_days)
        .subquery()
    )

    rows = (
        db.query(Candle1m.close)
        .join(
            day_subquery,
            and_(
                Candle1m.start_time == day_subquery.c.last_ts,
                func.date(Candle1m.start_time) == day_subquery.c.candle_day,
            ),
        )
        .filter(Candle1m.symbol == symbol)
        .order_by(Candle1m.start_time.desc())
        .all()
    )

    return [float(row[0]) for row in rows]


def _rsi_series_wilder(values_asc: List[float], period: int) -> List[float]:
    if len(values_asc) < period + 1:
        return []

    gains: List[float] = []
    losses: List[float] = []
    for index in range(1, period + 1):
        delta = values_asc[index] - values_asc[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    rsi_values: List[float] = []
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

    for index in range(period + 1, len(values_asc)):
        delta = values_asc[index] - values_asc[index - 1]
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)

        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

    return rsi_values


def _rsi_current_prev(values_desc: List[float], period: int) -> Tuple[Optional[float], Optional[float]]:
    values_asc = list(reversed(values_desc))
    rsi_values = _rsi_series_wilder(values_asc, period)
    if len(rsi_values) < 2:
        return None, None
    return rsi_values[-1], rsi_values[-2]


def run_rsi_crossover_screener(
    db: Session,
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if rsi_period < 2:
        raise ValueError("rsi_period must be >= 2")
    if rsi_level < 0 or rsi_level > 100:
        raise ValueError("rsi_level must be between 0 and 100")

    lookback_days = rsi_period + 120

    latest_query = db.query(
        LatestCandle1m.symbol,
        LatestCandle1m.open,
        LatestCandle1m.close,
        LatestCandle1m.updated_at,
    ).order_by(LatestCandle1m.symbol)

    if symbol_contains:
        latest_query = latest_query.filter(LatestCandle1m.symbol.ilike(f"%{symbol_contains.upper()}%"))

    latest_rows = latest_query.all()

    results = []
    for symbol, day_open, last_price, updated_at in latest_rows:
        closes_desc = _get_daily_closes_desc(db, symbol, lookback_days)
        if len(closes_desc) < rsi_period + 2:
            continue

        rsi_curr, rsi_prev = _rsi_current_prev(closes_desc, rsi_period)
        if rsi_curr is None or rsi_prev is None:
            continue

        crossed_above = rsi_prev <= rsi_level and rsi_curr > rsi_level
        crossed_below = rsi_prev >= rsi_level and rsi_curr < rsi_level

        if direction_l == "above" and not crossed_above:
            continue
        if direction_l == "below" and not crossed_below:
            continue

        prev_day_close = closes_desc[1] if len(closes_desc) > 1 else None
        percent_change = (
            ((last_price - prev_day_close) / prev_day_close) * 100
            if prev_day_close
            else None
        )

        results.append(
            {
                "symbol": symbol,
                "signal_date": str(updated_at.date()) if updated_at else None,
                "open": float(day_open),
                "last_price": float(last_price),
                "prev_day_close": float(prev_day_close) if prev_day_close is not None else None,
                "percent_change": round(percent_change, 2) if percent_change is not None else None,
                "rsi_period": rsi_period,
                "rsi_level": float(rsi_level),
                "rsi_prev": round(float(rsi_prev), 4),
                "rsi_curr": round(float(rsi_curr), 4),
                "direction": direction_l,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        )

    return results


def refresh_rsi_crossover_cache(
    db: Session,
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if rsi_period < 2:
        raise ValueError("rsi_period must be >= 2")
    if rsi_level < 0 or rsi_level > 100:
        raise ValueError("rsi_level must be between 0 and 100")

    rows = run_rsi_crossover_screener(
        db,
        rsi_period=rsi_period,
        rsi_level=rsi_level,
        direction=direction_l,
        symbol_contains=symbol_contains,
    )

    try:
        db.query(RSISignalCache).filter(
            RSISignalCache.rsi_period == rsi_period,
            RSISignalCache.rsi_level == float(rsi_level),
            RSISignalCache.direction == direction_l,
        ).delete(synchronize_session=False)

        now_ny = datetime.now(ZoneInfo("America/New_York"))
        for row in rows:
            signal_date = now_ny.date()
            if row.get("signal_date"):
                try:
                    signal_date = datetime.fromisoformat(row["signal_date"]).date()
                except Exception:
                    pass

            cache_row = RSISignalCache(
                symbol=row["symbol"],
                signal_date=signal_date,
                rsi_period=rsi_period,
                rsi_level=float(rsi_level),
                direction=direction_l,
                open=row.get("open"),
                last_price=row.get("last_price"),
                prev_day_close=row.get("prev_day_close"),
                percent_change=row.get("percent_change"),
                rsi_prev=row.get("rsi_prev"),
                rsi_curr=row.get("rsi_curr"),
                source_updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
                cached_at=now_ny,
            )
            db.add(cache_row)

        db.commit()
        return {
            "count": len(rows),
            "rsi_period": rsi_period,
            "rsi_level": float(rsi_level),
            "direction": direction_l,
        }
    except Exception:
        db.rollback()
        raise


def clear_rsi_crossover_cache(
    db: Session,
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if rsi_period < 2:
        raise ValueError("rsi_period must be >= 2")
    if rsi_level < 0 or rsi_level > 100:
        raise ValueError("rsi_level must be between 0 and 100")

    try:
        query = db.query(RSISignalCache).filter(
            RSISignalCache.rsi_period == rsi_period,
            RSISignalCache.rsi_level == float(rsi_level),
            RSISignalCache.direction == direction_l,
        )

        if symbol_contains:
            query = query.filter(RSISignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

        deleted = query.delete(synchronize_session=False)
        db.commit()
        return {
            "count": deleted,
            "rsi_period": rsi_period,
            "rsi_level": float(rsi_level),
            "direction": direction_l,
        }
    except Exception:
        db.rollback()
        raise


def get_rsi_crossover_cache(
    db: Session,
    rsi_period: int = 14,
    rsi_level: float = 59,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if rsi_period < 2:
        raise ValueError("rsi_period must be >= 2")
    if rsi_level < 0 or rsi_level > 100:
        raise ValueError("rsi_level must be between 0 and 100")

    query = db.query(RSISignalCache).filter(
        RSISignalCache.rsi_period == rsi_period,
        RSISignalCache.rsi_level == float(rsi_level),
        RSISignalCache.direction == direction_l,
    )

    if symbol_contains:
        query = query.filter(RSISignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

    rows = query.order_by(RSISignalCache.symbol).all()
    return [
        {
            "symbol": row.symbol,
            "signal_date": row.signal_date.isoformat() if row.signal_date else None,
            "open": row.open,
            "last_price": row.last_price,
            "prev_day_close": row.prev_day_close,
            "percent_change": row.percent_change,
            "rsi_period": row.rsi_period,
            "rsi_level": row.rsi_level,
            "rsi_prev": row.rsi_prev,
            "rsi_curr": row.rsi_curr,
            "direction": row.direction,
            "updated_at": row.source_updated_at.isoformat() if row.source_updated_at else None,
            "cached_at": row.cached_at.isoformat() if row.cached_at else None,
        }
        for row in rows
    ]
