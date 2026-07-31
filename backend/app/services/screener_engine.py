from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional

from app.models.latest_tick import LatestTick
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


def run_screener(db: Session):
    """
    Computes screener metrics for all symbols that have:
    - a latest tick
    - intraday candles for today
    """

    today = date.today()

    # Get all symbols that have a latest tick
    latest_ticks = db.query(LatestTick).all()
    results = []

    for lt in latest_ticks:
        sym = lt.symbol
        last_price = lt.price

        # Get today's candles for this symbol
        candles = (
            db.query(IntradayCandle)
            .filter(
                IntradayCandle.symbol == sym,
                func.date(IntradayCandle.timestamp) == today
            )
            .order_by(IntradayCandle.timestamp.desc())
            .limit(60)
            .all()
        )

        if not candles:
            continue

        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]

        open_price = closes[-1]
        percent_change = (
            (last_price - open_price) / open_price * 100
            if open_price > 0 else 0
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

        results.append({
            "symbol": sym,
            "last_price": last_price,
            "percent_change": round(percent_change, 2),
            "volume": total_volume,
            "rel_volume": round(rel_volume, 2),
            "high": high,
            "low": low,
            "vwap": round(vwap, 2),
            "sparkline": sparkline,
            "updated_at": lt.timestamp
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
        percent_change = (
            (last_price - open_price) / open_price * 100
            if open_price > 0 else 0
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
