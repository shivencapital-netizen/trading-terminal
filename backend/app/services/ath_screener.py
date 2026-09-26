from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.ath_signal_cache import ATHSignalCache
from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m


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


def _ath_current_prev(values_desc: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if not values_desc:
        return None, None, None

    current = float(values_desc[0])
    prev_close = float(values_desc[1]) if len(values_desc) > 1 else current
    previous_all_time_high = max(float(v) for v in values_desc[1:]) if len(values_desc) > 1 else current
    return current, prev_close, previous_all_time_high


def run_ath_screener(
    db: Session,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    min_history_days: int = 30,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if min_history_days < 2:
        raise ValueError("min_history_days must be >= 2")

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
        closes_desc = _get_daily_closes_desc(db, symbol, limit_days=max(min_history_days, 30))
        if len(closes_desc) < min_history_days:
            continue

        current_close, prev_day_close, previous_all_time_high = _ath_current_prev(closes_desc)
        if current_close is None or previous_all_time_high is None:
            continue

        crossed_above = prev_day_close <= previous_all_time_high and current_close > previous_all_time_high
        crossed_below = prev_day_close >= previous_all_time_high and current_close < previous_all_time_high

        if direction_l == "above" and not crossed_above:
            continue
        if direction_l == "below" and not crossed_below:
            continue

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
                "previous_all_time_high": round(float(previous_all_time_high), 4),
                "current_all_time_high": round(float(current_close), 4),
                "percent_change": round(percent_change, 2) if percent_change is not None else None,
                "direction": direction_l,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        )

    return results


def refresh_ath_screener_cache(
    db: Session,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    min_history_days: int = 30,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if min_history_days < 2:
        raise ValueError("min_history_days must be >= 2")

    rows = run_ath_screener(
        db,
        direction=direction_l,
        symbol_contains=symbol_contains,
        min_history_days=min_history_days,
    )

    try:
        db.query(ATHSignalCache).filter(
            ATHSignalCache.direction == direction_l,
        ).delete(synchronize_session=False)

        now_ny = datetime.now(ZoneInfo("America/New_York"))
        for row in rows:
            signal_date = now_ny.date()
            if row.get("signal_date"):
                try:
                    signal_date = datetime.fromisoformat(row["signal_date"]).date()
                except Exception:
                    pass

            cache_row = ATHSignalCache(
                symbol=row["symbol"],
                signal_date=signal_date,
                direction=direction_l,
                all_time_high=row.get("previous_all_time_high"),
                previous_high=row.get("previous_all_time_high"),
                prev_day_close=row.get("prev_day_close"),
                last_price=row.get("last_price"),
                percent_change=row.get("percent_change"),
                source_updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
                cached_at=now_ny,
            )
            db.add(cache_row)

        db.commit()
        return {
            "count": len(rows),
            "direction": direction_l,
            "min_history_days": min_history_days,
        }
    except Exception:
        db.rollback()
        raise


def clear_ath_screener_cache(
    db: Session,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    min_history_days: int = 30,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if min_history_days < 2:
        raise ValueError("min_history_days must be >= 2")

    try:
        query = db.query(ATHSignalCache).filter(ATHSignalCache.direction == direction_l)
        if symbol_contains:
            query = query.filter(ATHSignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

        deleted = query.delete(synchronize_session=False)
        db.commit()
        return {
            "count": deleted,
            "direction": direction_l,
            "min_history_days": min_history_days,
        }
    except Exception:
        db.rollback()
        raise


def get_ath_screener_cache(
    db: Session,
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    min_history_days: int = 30,
):
    direction_l = direction.lower()
    if direction_l not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if min_history_days < 2:
        raise ValueError("min_history_days must be >= 2")

    query = db.query(ATHSignalCache).filter(ATHSignalCache.direction == direction_l)
    if symbol_contains:
        query = query.filter(ATHSignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

    rows = query.order_by(ATHSignalCache.symbol).all()
    return [
        {
            "symbol": row.symbol,
            "signal_date": row.signal_date.isoformat() if row.signal_date else None,
            "all_time_high": row.all_time_high,
            "previous_high": row.previous_high,
            "prev_day_close": row.prev_day_close,
            "last_price": row.last_price,
            "percent_change": row.percent_change,
            "direction": row.direction,
            "updated_at": row.source_updated_at.isoformat() if row.source_updated_at else None,
            "cached_at": row.cached_at.isoformat() if row.cached_at else None,
        }
        for row in rows
    ]
