from datetime import datetime, time
import os
from zoneinfo import ZoneInfo

import requests
from sqlalchemy.orm import Session

from app.core.market_hours import is_regular_market_hours
from app.models.instrument import Instrument
from app.models.intraday import IntradayCandle
from app.models.intraday_rsi_monitor import IntradayRsiAlert, IntradayRsiMonitor

EASTERN_TZ = ZoneInfo("America/New_York")


def _rsi_values(closes: list[float], period: int) -> list[float | None]:
    values: list[float | None] = [None] * len(closes)
    if len(closes) <= period:
        return values

    gains = [max(closes[index] - closes[index - 1], 0.0) for index in range(1, len(closes))]
    losses = [max(closes[index - 1] - closes[index], 0.0) for index in range(1, len(closes))]
    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period

    def value() -> float:
        if average_loss == 0:
            return 100.0
        if average_gain == 0:
            return 0.0
        return 100.0 - (100.0 / (1.0 + average_gain / average_loss))

    values[period] = value()
    for index in range(period, len(gains)):
        average_gain = ((average_gain * (period - 1)) + gains[index]) / period
        average_loss = ((average_loss * (period - 1)) + losses[index]) / period
        values[index + 1] = value()
    return values


def _monitor_symbols(db: Session, monitor: IntradayRsiMonitor) -> list[str]:
    configured = [str(symbol).strip().upper() for symbol in (monitor.symbols or []) if str(symbol).strip()]
    if "ALL" not in configured:
        return sorted(set(configured))
    return [row[0].upper() for row in db.query(Instrument.symbol).order_by(Instrument.symbol).all() if row[0]]


def _send_sms(monitor: IntradayRsiMonitor, alert: IntradayRsiAlert) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    if not all((account_sid, auth_token, from_number, monitor.sms_phone)):
        raise RuntimeError("SMS is enabled but Twilio credentials/from number/recipient are not configured.")

    direction = "crossed above" if alert.direction == "up" else "crossed below"
    body = (
        f"{alert.symbol} RSI({alert.rsi_period}) {direction} {alert.rsi_level:g}: "
        f"{alert.rsi_previous:.2f} -> {alert.rsi_current:.2f} at "
        f"{alert.candle_timestamp.strftime('%H:%M ET')} (close ${alert.close:.2f})"
    )
    response = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        data={"To": monitor.sms_phone, "From": from_number, "Body": body},
        auth=(account_sid, auth_token),
        timeout=(3, 10),
    )
    response.raise_for_status()


def evaluate_active_monitors(db: Session) -> int:
    if not is_regular_market_hours():
        return 0

    now = datetime.now(EASTERN_TZ).replace(tzinfo=None)
    session_start = datetime.combine(now.date(), time(9, 30))
    alerts_created = 0
    monitors = db.query(IntradayRsiMonitor).filter(IntradayRsiMonitor.is_active.is_(True)).all()

    for monitor in monitors:
        try:
            for symbol in _monitor_symbols(db, monitor):
                candles = (
                    db.query(IntradayCandle)
                    .filter(
                        IntradayCandle.symbol == symbol,
                        IntradayCandle.timeframe == "1m",
                        IntradayCandle.timestamp >= session_start,
                        IntradayCandle.timestamp <= now,
                    )
                    .order_by(IntradayCandle.timestamp)
                    .all()
                )
                if len(candles) <= monitor.rsi_period:
                    continue

                closes = [float(candle.close) for candle in candles]
                rsi = _rsi_values(closes, monitor.rsi_period)
                current = rsi[-1]
                previous = rsi[-2]
                if current is None or previous is None:
                    continue

                crossings = []
                if monitor.direction in ("both", "up") and previous < monitor.rsi_level <= current:
                    crossings.append("up")
                if monitor.direction in ("both", "down") and previous > monitor.rsi_level >= current:
                    crossings.append("down")

                for direction in crossings:
                    candle = candles[-1]
                    exists = db.query(IntradayRsiAlert.id).filter(
                        IntradayRsiAlert.monitor_id == monitor.id,
                        IntradayRsiAlert.symbol == symbol,
                        IntradayRsiAlert.direction == direction,
                        IntradayRsiAlert.candle_timestamp == candle.timestamp,
                    ).first()
                    if exists:
                        continue

                    alert = IntradayRsiAlert(
                        monitor_id=monitor.id,
                        symbol=symbol,
                        direction=direction,
                        rsi_period=monitor.rsi_period,
                        rsi_level=monitor.rsi_level,
                        rsi_previous=round(previous, 4),
                        rsi_current=round(current, 4),
                        close=round(float(candle.close), 4),
                        candle_timestamp=candle.timestamp,
                    )
                    db.add(alert)
                    db.commit()
                    db.refresh(alert)
                    alerts_created += 1
                    if monitor.sms_enabled:
                        try:
                            _send_sms(monitor, alert)
                        except Exception as sms_error:
                            monitor.last_error = f"SMS error: {sms_error}"
                            db.commit()

            monitor.last_checked_at = now
            monitor.last_error = None
            db.commit()
        except Exception as error:
            db.rollback()
            monitor.last_error = str(error)[:1000]
            monitor.last_checked_at = now
            db.commit()

    return alerts_created


def start_intraday_rsi_monitoring(interval_seconds: int = 60) -> None:
    from app.db.session import SessionLocal
    import time as time_module

    while True:
        db = SessionLocal()
        try:
            created = evaluate_active_monitors(db)
            if created:
                print(f"📣 Intraday RSI alerts created: {created}")
        except Exception as error:
            print(f"❌ Intraday RSI monitor error: {error}")
        finally:
            db.close()
        time_module.sleep(interval_seconds)
