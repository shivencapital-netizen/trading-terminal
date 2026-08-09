from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m
from app.models.ma_signal_cache import MASignalCache


MA_TYPES = {"SMA", "EMA", "WMA"}
DIRECTIONS = {"above", "below"}
MA_PERIOD_OPTIONS = [5, 10, 20, 50, 100, 200]


def _sma_desc(values_desc: List[float], period: int, offset: int = 0) -> Optional[float]:
    window = values_desc[offset : offset + period]
    if len(window) < period:
        return None
    return sum(window) / period


def _wma_desc(values_desc: List[float], period: int, offset: int = 0) -> Optional[float]:
    window = values_desc[offset : offset + period]
    if len(window) < period:
        return None
    weights = list(range(period, 0, -1))
    weighted_sum = sum(v * w for v, w in zip(window, weights))
    return weighted_sum / sum(weights)


def _ema_last_two_desc(values_desc: List[float], period: int) -> Tuple[Optional[float], Optional[float]]:
    if len(values_desc) < period + 1:
        return None, None

    values_asc = list(reversed(values_desc))
    seed = sum(values_asc[:period]) / period
    k = 2 / (period + 1)

    ema_values = [seed]
    for price in values_asc[period:]:
        ema_values.append((price * k) + (ema_values[-1] * (1 - k)))

    if len(ema_values) < 2:
        return None, None

    prev_ema = ema_values[-2]
    curr_ema = ema_values[-1]
    return curr_ema, prev_ema


def _ma_current_prev(values_desc: List[float], period: int, ma_type: str) -> Tuple[Optional[float], Optional[float]]:
    ma_type = ma_type.upper()
    if ma_type == "SMA":
        return _sma_desc(values_desc, period, 0), _sma_desc(values_desc, period, 1)
    if ma_type == "WMA":
        return _wma_desc(values_desc, period, 0), _wma_desc(values_desc, period, 1)
    if ma_type == "EMA":
        return _ema_last_two_desc(values_desc, period)
    return None, None


def _family_period_pairs() -> List[Tuple[int, int]]:
    return [
        (fast_period, slow_period)
        for fast_index, fast_period in enumerate(MA_PERIOD_OPTIONS)
        for slow_period in MA_PERIOD_OPTIONS[fast_index + 1 :]
    ]


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


def run_ma_crossover_screener(
    db: Session,
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: Optional[str] = None,
):
    fast_ma = fast_ma.upper()
    slow_ma = slow_ma.upper()
    direction = direction.lower()

    if fast_ma not in MA_TYPES:
        raise ValueError(f"Unsupported fast_ma '{fast_ma}'. Use one of {sorted(MA_TYPES)}")
    if slow_ma not in MA_TYPES:
        raise ValueError(f"Unsupported slow_ma '{slow_ma}'. Use one of {sorted(MA_TYPES)}")
    if direction not in DIRECTIONS:
        raise ValueError("direction must be 'above' or 'below'")
    if fast_period < 2 or slow_period < 2:
        raise ValueError("periods must be >= 2")

    lookback_days = max(fast_period, slow_period) + 120

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
        if len(closes_desc) < max(fast_period, slow_period) + 1:
            continue

        fast_curr, fast_prev = _ma_current_prev(closes_desc, fast_period, fast_ma)
        slow_curr, slow_prev = _ma_current_prev(closes_desc, slow_period, slow_ma)

        if None in (fast_curr, fast_prev, slow_curr, slow_prev):
            continue

        crossed_above = fast_prev <= slow_prev and fast_curr > slow_curr
        crossed_below = fast_prev >= slow_prev and fast_curr < slow_curr

        if direction == "above" and not crossed_above:
            continue
        if direction == "below" and not crossed_below:
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
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "fast_prev": round(float(fast_prev), 4),
                "fast_curr": round(float(fast_curr), 4),
                "slow_prev": round(float(slow_prev), 4),
                "slow_curr": round(float(slow_curr), 4),
                "direction": direction,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        )

    return results


def refresh_ma_crossover_cache(
    db: Session,
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    ma_family: Optional[str] = None,
):
    def _refresh_single_combo(
        combo_fast_period: int,
        combo_slow_period: int,
        combo_fast_ma: str,
        combo_slow_ma: str,
    ) -> int:
        rows = run_ma_crossover_screener(
            db,
            fast_period=combo_fast_period,
            slow_period=combo_slow_period,
            fast_ma=combo_fast_ma,
            slow_ma=combo_slow_ma,
            direction=direction_l,
            symbol_contains=symbol_contains,
        )

        db.query(MASignalCache).filter(
            MASignalCache.fast_ma == combo_fast_ma,
            MASignalCache.slow_ma == combo_slow_ma,
            MASignalCache.fast_period == combo_fast_period,
            MASignalCache.slow_period == combo_slow_period,
            MASignalCache.direction == direction_l,
        ).delete(synchronize_session=False)

        now_ny = datetime.now(ZoneInfo("America/New_York"))
        for row in rows:
            signal_date = now_ny.date()
            if row.get("signal_date"):
                try:
                    signal_date = datetime.fromisoformat(row["signal_date"]).date()
                except Exception:
                    pass

            cache_row = MASignalCache(
                symbol=row["symbol"],
                signal_date=signal_date,
                fast_ma=combo_fast_ma,
                slow_ma=combo_slow_ma,
                fast_period=combo_fast_period,
                slow_period=combo_slow_period,
                direction=direction_l,
                open=row.get("open"),
                last_price=row.get("last_price"),
                prev_day_close=row.get("prev_day_close"),
                percent_change=row.get("percent_change"),
                fast_prev=row.get("fast_prev"),
                fast_curr=row.get("fast_curr"),
                slow_prev=row.get("slow_prev"),
                slow_curr=row.get("slow_curr"),
                source_updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
                cached_at=now_ny,
            )
            db.add(cache_row)

        return len(rows)

    fast_ma_u = fast_ma.upper()
    slow_ma_u = slow_ma.upper()
    direction_l = direction.lower()

    try:
        if ma_family:
            family = ma_family.upper()
            if family not in MA_TYPES:
                raise ValueError(f"Unsupported ma_family '{family}'. Use one of {sorted(MA_TYPES)}")

            total_count = 0
            combos = _family_period_pairs()
            for combo_fast_period, combo_slow_period in combos:
                total_count += _refresh_single_combo(combo_fast_period, combo_slow_period, family, family)

            db.commit()
            return {
                "count": total_count,
                "fast_ma": family,
                "slow_ma": family,
                "direction": direction_l,
                "ma_family": family,
                "combinations": len(combos),
            }

        if fast_ma_u not in MA_TYPES:
            raise ValueError(f"Unsupported fast_ma '{fast_ma_u}'. Use one of {sorted(MA_TYPES)}")
        if slow_ma_u not in MA_TYPES:
            raise ValueError(f"Unsupported slow_ma '{slow_ma_u}'. Use one of {sorted(MA_TYPES)}")

        count = _refresh_single_combo(fast_period, slow_period, fast_ma_u, slow_ma_u)
        db.commit()
        return {
            "count": count,
            "fast_ma": fast_ma_u,
            "slow_ma": slow_ma_u,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "direction": direction_l,
        }
    except Exception:
        db.rollback()
        raise


def clear_ma_crossover_cache(
    db: Session,
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    ma_family: Optional[str] = None,
):
    fast_ma_u = fast_ma.upper()
    slow_ma_u = slow_ma.upper()
    direction_l = direction.lower()

    try:
        if ma_family:
            family = ma_family.upper()
            if family not in MA_TYPES:
                raise ValueError(f"Unsupported ma_family '{family}'. Use one of {sorted(MA_TYPES)}")

            combos = _family_period_pairs()
            total_deleted = 0
            for combo_fast_period, combo_slow_period in combos:
                query = db.query(MASignalCache).filter(
                    MASignalCache.fast_ma == family,
                    MASignalCache.slow_ma == family,
                    MASignalCache.fast_period == combo_fast_period,
                    MASignalCache.slow_period == combo_slow_period,
                    MASignalCache.direction == direction_l,
                )
                if symbol_contains:
                    query = query.filter(MASignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))
                total_deleted += query.delete(synchronize_session=False)

            db.commit()
            return {
                "count": total_deleted,
                "fast_ma": family,
                "slow_ma": family,
                "direction": direction_l,
                "ma_family": family,
                "combinations": len(combos),
            }

        if fast_ma_u not in MA_TYPES:
            raise ValueError(f"Unsupported fast_ma '{fast_ma_u}'. Use one of {sorted(MA_TYPES)}")
        if slow_ma_u not in MA_TYPES:
            raise ValueError(f"Unsupported slow_ma '{slow_ma_u}'. Use one of {sorted(MA_TYPES)}")

        query = db.query(MASignalCache).filter(
            MASignalCache.fast_ma == fast_ma_u,
            MASignalCache.slow_ma == slow_ma_u,
            MASignalCache.fast_period == fast_period,
            MASignalCache.slow_period == slow_period,
            MASignalCache.direction == direction_l,
        )
        if symbol_contains:
            query = query.filter(MASignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

        deleted = query.delete(synchronize_session=False)
        db.commit()
        return {
            "count": deleted,
            "fast_ma": fast_ma_u,
            "slow_ma": slow_ma_u,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "direction": direction_l,
        }
    except Exception:
        db.rollback()
        raise


def get_ma_crossover_cache(
    db: Session,
    fast_period: int = 10,
    slow_period: int = 20,
    fast_ma: str = "SMA",
    slow_ma: str = "SMA",
    direction: str = "above",
    symbol_contains: Optional[str] = None,
    ma_family: Optional[str] = None,
):
    direction_l = direction.lower()

    if ma_family:
        family = ma_family.upper()
        if family not in MA_TYPES:
            raise ValueError(f"Unsupported ma_family '{family}'. Use one of {sorted(MA_TYPES)}")

        query = db.query(MASignalCache).filter(
            MASignalCache.fast_ma == family,
            MASignalCache.slow_ma == family,
            MASignalCache.direction == direction_l,
        )
    else:
        query = db.query(MASignalCache).filter(
            MASignalCache.fast_ma == fast_ma.upper(),
            MASignalCache.slow_ma == slow_ma.upper(),
            MASignalCache.fast_period == fast_period,
            MASignalCache.slow_period == slow_period,
            MASignalCache.direction == direction_l,
        )

    if symbol_contains:
        query = query.filter(MASignalCache.symbol.ilike(f"%{symbol_contains.upper()}%"))

    if ma_family:
        rows = query.order_by(
            MASignalCache.fast_period,
            MASignalCache.slow_period,
            MASignalCache.symbol,
        ).all()
    else:
        rows = query.order_by(MASignalCache.symbol).all()
    return [
        {
            "symbol": row.symbol,
            "signal_date": row.signal_date.isoformat() if row.signal_date else None,
            "open": row.open,
            "last_price": row.last_price,
            "prev_day_close": row.prev_day_close,
            "percent_change": row.percent_change,
            "fast_ma": row.fast_ma,
            "slow_ma": row.slow_ma,
            "fast_period": row.fast_period,
            "slow_period": row.slow_period,
            "fast_prev": row.fast_prev,
            "fast_curr": row.fast_curr,
            "slow_prev": row.slow_prev,
            "slow_curr": row.slow_curr,
            "direction": row.direction,
            "updated_at": row.source_updated_at.isoformat() if row.source_updated_at else None,
            "cached_at": row.cached_at.isoformat() if row.cached_at else None,
        }
        for row in rows
    ]
