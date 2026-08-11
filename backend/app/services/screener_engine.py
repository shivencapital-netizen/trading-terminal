from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.core.market_hours import ny_now
from app.models.intraday import IntradayCandle
from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m
from app.models.history_screener import HistoryScreenerRun, HistoryScreenerResult
from app.schemas.screener import ScreenerFilters


def get_sparkline(candles, limit=30):
    """
    Extracts the last N close prices from today's intraday candles.
    Returns them in chronological order for sparkline charts.
    """
    closes = [c.close for c in candles][:limit]  # candles already sorted DESC
    return closes[::-1]  # reverse to chronological


def get_previous_day_last_close(db: Session, symbol: str, session_date: date):
    """Return the latest 1m close before the provided session date."""
    row = (
        db.query(Candle1m.close)
        .filter(
            Candle1m.symbol == symbol,
            func.date(Candle1m.start_time) < session_date,
        )
        .order_by(Candle1m.start_time.desc())
        .first()
    )
    return float(row[0]) if row else None


def get_previous_n_day_high(db: Session, symbol: str, session_date: date, days: int = 5):
    """Return the highest intraday high across the prior N trading days (excluding session_date)."""
    rows = (
        db.query(
            func.date(Candle1m.start_time).label("session_day"),
            func.max(Candle1m.high).label("day_high"),
        )
        .filter(
            Candle1m.symbol == symbol,
            func.date(Candle1m.start_time) < session_date,
        )
        .group_by(func.date(Candle1m.start_time))
        .order_by(func.date(Candle1m.start_time).desc())
        .limit(days)
        .all()
    )
    highs = [float(row[1]) for row in rows if row[1] is not None]
    return max(highs) if highs else None


def get_previous_n_day_highs_bulk(db: Session, symbols: list[str], session_date: date, days: int):
    """Return {symbol: highest high across prior N trading days}, computed in bulk."""
    if not symbols:
        return {}

    day_field = func.date(Candle1m.start_time)

    daily_highs = (
        db.query(
            Candle1m.symbol.label("symbol"),
            day_field.label("session_day"),
            func.max(Candle1m.high).label("day_high"),
        )
        .filter(
            Candle1m.symbol.in_(symbols),
            day_field < session_date,
        )
        .group_by(Candle1m.symbol, day_field)
        .subquery()
    )

    ranked = (
        db.query(
            daily_highs.c.symbol,
            daily_highs.c.day_high,
            func.row_number()
            .over(
                partition_by=daily_highs.c.symbol,
                order_by=daily_highs.c.session_day.desc(),
            )
            .label("rn"),
        )
        .subquery()
    )

    rows = (
        db.query(
            ranked.c.symbol,
            func.max(ranked.c.day_high).label("n_day_high"),
        )
        .filter(ranked.c.rn <= max(1, int(days)))
        .group_by(ranked.c.symbol)
        .all()
    )

    return {row[0]: float(row[1]) for row in rows if row[1] is not None}


def run_screener(db: Session, filters: Optional[ScreenerFilters] = None):
    """
    Computes screener metrics for all symbols that have:
    - a latest tick
    - intraday candles for today
    """

    now = ny_now().replace(tzinfo=None)
    today = now.date()

    # Use today's intraday coverage as the source of truth for the live screener.
    live_symbols = [
        row[0]
        for row in (
            db.query(IntradayCandle.symbol)
            .filter(func.date(IntradayCandle.timestamp) == today)
            .filter(IntradayCandle.timestamp <= now)
            .distinct()
            .all()
        )
        if row and row[0]
    ]
    results = []

    for sym in live_symbols:
        if filters is not None and filters.symbol and filters.symbol.upper() not in sym.upper():
            continue

        # Get today's candles for this symbol
        candles = (
            db.query(IntradayCandle)
            .filter(
                IntradayCandle.symbol == sym,
                func.date(IntradayCandle.timestamp) == today,
                IntradayCandle.timestamp <= now,
            )
            .order_by(IntradayCandle.timestamp.desc())
            .limit(60)
            .all()
        )

        if not candles:
            continue

        volumes = [c.volume for c in candles]

        latest_candle = candles[0]
        last_price = latest_candle.close
        open_price = candles[-1].open
        session_date = candles[0].timestamp.date()
        reference_close = get_previous_day_last_close(db, sym, session_date) or open_price
        percent_change = (
            (last_price - reference_close) / reference_close * 100
            if reference_close > 0 else 0
        )

        total_volume = sum(volumes)
        avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else total_volume
        rel_volume = total_volume / avg_volume if avg_volume > 0 else 1

        high = max(c.high for c in candles)
        low = min(c.low for c in candles)
        vwap = (
            sum(c.close * c.volume for c in candles) /
            sum(c.volume for c in candles)
            if sum(c.volume for c in candles) > 0 else last_price
        )

        sparkline = get_sparkline(candles, limit=30)

        if filters is not None:
            if filters.min_price is not None and last_price < filters.min_price:
                continue
            if filters.max_price is not None and last_price > filters.max_price:
                continue
            if filters.min_volume is not None and total_volume < filters.min_volume:
                continue
            if filters.price_above_5d_high:
                prev_5d_high = get_previous_n_day_high(db, sym, session_date, days=5)
                if prev_5d_high is None or last_price <= prev_5d_high:
                    continue

        results.append({
            "symbol": sym,
            "open": open_price,
            "last_price": last_price,
            "percent_change": round(percent_change, 2),
            "volume": total_volume,
            "rel_volume": round(rel_volume, 2),
            "high": high,
            "low": low,
            "vwap": round(vwap, 2),
            "sparkline": sparkline,
            "updated_at": latest_candle.timestamp
        })

    return results


def run_breakout_screener(db: Session, lookback_days: int = 5):
    """
    Separate breakout calculation for symbols whose live price is above prior N-day high.
    Uses today's intraday candles for current price and candles_1m for prior-day highs.
    """
    now = ny_now().replace(tzinfo=None)
    today = now.date()
    lookback_days = max(1, min(int(lookback_days or 5), 120))

    live_symbols = [
        row[0]
        for row in (
            db.query(IntradayCandle.symbol)
            .filter(func.date(IntradayCandle.timestamp) == today)
            .filter(IntradayCandle.timestamp <= now)
            .distinct()
            .all()
        )
        if row and row[0]
    ]

    prev_high_map = get_previous_n_day_highs_bulk(db, live_symbols, today, lookback_days)
    results = []

    for sym in live_symbols:
        candles = (
            db.query(IntradayCandle)
            .filter(
                IntradayCandle.symbol == sym,
                func.date(IntradayCandle.timestamp) == today,
                IntradayCandle.timestamp <= now,
            )
            .order_by(IntradayCandle.timestamp.desc())
            .limit(60)
            .all()
        )

        if not candles:
            continue

        latest_candle = candles[0]
        last_price = latest_candle.close
        prev_high = prev_high_map.get(sym)
        if prev_high is None or last_price <= prev_high:
            continue

        breakout_happened_at = (
            db.query(func.min(IntradayCandle.timestamp))
            .filter(
                IntradayCandle.symbol == sym,
                func.date(IntradayCandle.timestamp) == today,
                IntradayCandle.timestamp <= now,
                IntradayCandle.high > prev_high,
            )
            .scalar()
        )

        volumes = [c.volume for c in candles]
        open_price = candles[-1].open
        session_date = candles[0].timestamp.date()
        reference_close = get_previous_day_last_close(db, sym, session_date) or open_price
        percent_change = (
            (last_price - reference_close) / reference_close * 100
            if reference_close > 0 else 0
        )

        high = max(c.high for c in candles)
        low = min(c.low for c in candles)
        vwap = (
            sum(c.close * c.volume for c in candles) /
            sum(c.volume for c in candles)
            if sum(c.volume for c in candles) > 0 else last_price
        )

        results.append({
            "symbol": sym,
            "open": open_price,
            "last_price": last_price,
            "percent_change": round(percent_change, 2),
            "volume": sum(volumes),
            "rel_volume": None,
            "high": high,
            "low": low,
            "vwap": round(vwap, 2),
            "sparkline": get_sparkline(candles, limit=30),
            "updated_at": latest_candle.timestamp,
            "breakout_lookback_days": lookback_days,
            "breakout_reference_high": round(prev_high, 2),
            "breakout_happened_at": breakout_happened_at.isoformat() if breakout_happened_at else None,
        })

    return results


def compute_sma(values, period):
    if len(values) < period:
        return None
    return sum(values[:period]) / period


def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, period + 1):
        change = closes[i - 1] - closes[i]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def score_history_screener(closes, volumes, last_price):
    sma_20 = compute_sma(closes, 20)
    sma_50 = compute_sma(closes, 50)
    avg_vol_20 = sum(volumes[:20]) / 20 if len(volumes) >= 20 else None
    rsi = compute_rsi(closes, period=14)
    score = 0

    if sma_20 and last_price > sma_20:
        score += 1
    if sma_50 and last_price > sma_50:
        score += 1
    if avg_vol_20 and volumes[0] > avg_vol_20:
        score += 1
    if rsi is not None and 50 <= rsi <= 70:
        score += 1

    return score, {"sma_20": sma_20, "sma_50": sma_50, "rsi_14": rsi, "avg_vol_20": avg_vol_20}


def is_sma_bullish_crossover(closes):
    if len(closes) < 51:
        return False

    current_20 = compute_sma(closes[0:20], 20)
    current_50 = compute_sma(closes[0:50], 50)
    previous_20 = compute_sma(closes[1:21], 20)
    previous_50 = compute_sma(closes[1:51], 50)

    if None in (current_20, current_50, previous_20, previous_50):
        return False

    return previous_20 <= previous_50 and current_20 > current_50


def is_rsi_bullish_divergence(closes, lookback=10):
    if len(closes) < lookback + 15:
        return False

    latest_rsi = compute_rsi(closes, period=14)
    previous_rsi = compute_rsi(closes[lookback:], period=14)

    if latest_rsi is None or previous_rsi is None:
        return False

    return closes[0] < closes[lookback] and latest_rsi > previous_rsi


def run_history_screener(db: Session, filters: Optional[ScreenerFilters] = None):
    """
    Computes screener metrics from the history candles_1m table.
    """

    run = HistoryScreenerRun(config=filters.dict() if filters else None)
    db.add(run)
    db.flush()

    query = db.query(LatestCandle1m)

    if filters is not None and filters.symbol:
        query = query.filter(LatestCandle1m.symbol.ilike(f"%{filters.symbol}%"))

    results = []
    latest_rows = query.order_by(LatestCandle1m.symbol).all()

    for latest in latest_rows:
        sym = latest.symbol
        last_price = latest.close

        candles = (
            db.query(Candle1m)
            .filter(Candle1m.symbol == sym)
            .order_by(Candle1m.start_time.desc())
            .limit(200)
            .all()
        )

        if not candles:
            continue

        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]

        open_price = closes[-1]
        session_date = latest.start_time.date()
        reference_close = get_previous_day_last_close(db, sym, session_date) or open_price
        percent_change = (
            (last_price - reference_close) / reference_close * 100
            if reference_close > 0 else 0
        )

        total_volume = sum(volumes[:60])
        avg_volume = sum(volumes[:20]) / 20 if len(volumes) >= 20 else total_volume
        vwap = (
            sum(c.close * c.volume for c in candles[:60]) /
            sum(c.volume for c in candles[:60])
            if sum(c.volume for c in candles[:60]) > 0 else last_price
        )

        score, extra_data = score_history_screener(closes, volumes, last_price)
        volume_ratio = None
        if avg_volume > 0:
            volume_ratio = total_volume / avg_volume

        sma_20 = extra_data.get("sma_20")
        sma_50 = extra_data.get("sma_50")
        prev_5d_high = get_previous_n_day_high(db, sym, session_date, days=5)
        rsi = extra_data.get("rsi_14")
        sma_cross = is_sma_bullish_crossover(closes)
        rsi_diverge = is_rsi_bullish_divergence(closes)

        if filters is not None:
            if filters.min_price is not None and last_price < filters.min_price:
                continue
            if filters.max_price is not None and last_price > filters.max_price:
                continue
            if filters.min_volume is not None and total_volume < filters.min_volume:
                continue
            if filters.price_above_sma20 and sma_20 is not None and last_price <= sma_20:
                continue
            if filters.price_above_sma50 and sma_50 is not None and last_price <= sma_50:
                continue
            if filters.price_above_5d_high and (prev_5d_high is None or last_price <= prev_5d_high):
                continue
            if filters.sma_bullish_crossover and not sma_cross:
                continue
            if filters.rsi_min is not None and (rsi is None or rsi < filters.rsi_min):
                continue
            if filters.rsi_max is not None and (rsi is None or rsi > filters.rsi_max):
                continue
            if filters.rsi_bullish_divergence and not rsi_diverge:
                continue
            if filters.avg_volume_ratio_min is not None and (volume_ratio is None or volume_ratio < filters.avg_volume_ratio_min):
                continue
            if filters.min_score is not None and score < filters.min_score:
                continue

        result = {
            "symbol": sym,
            "open": open_price,
            "last_price": last_price,
            "percent_change": round(percent_change, 2),
            "volume": total_volume,
            "high": max(c.high for c in candles[:60]),
            "low": min(c.low for c in candles[:60]),
            "vwap": round(vwap, 2),
            "sparkline": get_sparkline(candles, limit=30),
            "score": score,
            "rsi": rsi,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_bullish_crossover": sma_cross,
            "rsi_bullish_divergence": rsi_diverge,
            "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
            "data": extra_data,
            "updated_at": latest.updated_at,
        }

        results.append(result)

        db.add(HistoryScreenerResult(
            history_screener_run_id=run.id,
            symbol=sym,
            scan_date=latest.updated_at,
            last_price=last_price,
            volume=total_volume,
            high=max(c.high for c in candles[:60]),
            low=min(c.low for c in candles[:60]),
            vwap=round(vwap, 2),
            percent_change=round(percent_change, 2),
            score=score,
            data=extra_data,
            sparkline=result["sparkline"],
        ))

    run.completed_at = func.now()
    db.commit()

    return results
