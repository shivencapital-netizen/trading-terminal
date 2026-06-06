from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.models.latest_tick import LatestTick
from app.models.intraday import IntradayCandle


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

        # ⭐ NEW: Sparkline support
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
