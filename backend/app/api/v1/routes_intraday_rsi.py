from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.intraday_rsi_monitor import IntradayRsiAlert, IntradayRsiMonitor

router = APIRouter()


class MonitorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    symbols: list[str] = Field(min_length=1, max_length=500)
    rsi_period: int = Field(default=14, ge=2, le=100)
    rsi_level: float = Field(default=59, ge=0, le=100)
    direction: Literal["both", "up", "down"] = "both"
    sms_enabled: bool = False
    sms_phone: str | None = Field(default=None, max_length=32)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        normalized = sorted(set(symbol.strip().upper() for symbol in symbols if symbol.strip()))
        if not normalized:
            raise ValueError("At least one symbol is required.")
        return normalized


class MonitorUpdate(MonitorRequest):
    pass


def _serialize_monitor(monitor: IntradayRsiMonitor) -> dict:
    return {
        "id": monitor.id,
        "name": monitor.name,
        "symbols": monitor.symbols,
        "rsi_period": monitor.rsi_period,
        "rsi_level": monitor.rsi_level,
        "direction": monitor.direction,
        "sms_enabled": monitor.sms_enabled,
        "sms_phone": monitor.sms_phone,
        "is_active": monitor.is_active,
        "last_checked_at": monitor.last_checked_at.isoformat() if monitor.last_checked_at else None,
        "last_error": monitor.last_error,
        "created_at": monitor.created_at.isoformat() if monitor.created_at else None,
    }


def _serialize_alert(alert: IntradayRsiAlert) -> dict:
    return {
        "id": alert.id,
        "monitor_id": alert.monitor_id,
        "symbol": alert.symbol,
        "direction": alert.direction,
        "rsi_period": alert.rsi_period,
        "rsi_level": alert.rsi_level,
        "rsi_previous": alert.rsi_previous,
        "rsi_current": alert.rsi_current,
        "close": alert.close,
        "candle_timestamp": alert.candle_timestamp.isoformat(),
        "created_at": alert.created_at.isoformat(),
    }


@router.get("/monitors")
def list_monitors(db: Session = Depends(get_db)):
    monitors = db.query(IntradayRsiMonitor).order_by(IntradayRsiMonitor.created_at.desc()).all()
    return [_serialize_monitor(monitor) for monitor in monitors]


@router.post("/monitors", status_code=201)
def create_monitor(request: MonitorRequest, db: Session = Depends(get_db)):
    monitor = IntradayRsiMonitor(**request.model_dump())
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return _serialize_monitor(monitor)


@router.put("/monitors/{monitor_id}")
def update_monitor(monitor_id: int, request: MonitorUpdate, db: Session = Depends(get_db)):
    monitor = db.query(IntradayRsiMonitor).filter(IntradayRsiMonitor.id == monitor_id).first()
    if monitor is None:
        raise HTTPException(status_code=404, detail="RSI monitor not found.")
    for key, value in request.model_dump().items():
        setattr(monitor, key, value)
    db.commit()
    db.refresh(monitor)
    return _serialize_monitor(monitor)


@router.delete("/monitors/{monitor_id}")
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(IntradayRsiMonitor).filter(IntradayRsiMonitor.id == monitor_id).first()
    if monitor is None:
        raise HTTPException(status_code=404, detail="RSI monitor not found.")
    db.delete(monitor)
    db.query(IntradayRsiAlert).filter(IntradayRsiAlert.monitor_id == monitor_id).delete()
    db.commit()
    return {"id": monitor_id, "deleted": True}


@router.post("/monitors/{monitor_id}/start")
def start_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(IntradayRsiMonitor).filter(IntradayRsiMonitor.id == monitor_id).first()
    if monitor is None:
        raise HTTPException(status_code=404, detail="RSI monitor not found.")
    monitor.is_active = True
    monitor.last_error = None
    db.commit()
    return _serialize_monitor(monitor)


@router.post("/monitors/{monitor_id}/stop")
def stop_monitor(monitor_id: int, db: Session = Depends(get_db)):
    monitor = db.query(IntradayRsiMonitor).filter(IntradayRsiMonitor.id == monitor_id).first()
    if monitor is None:
        raise HTTPException(status_code=404, detail="RSI monitor not found.")
    monitor.is_active = False
    db.commit()
    return _serialize_monitor(monitor)


@router.get("/alerts")
def list_alerts(limit: int = 100, monitor_id: int | None = None, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 500)
    query = db.query(IntradayRsiAlert)
    if monitor_id is not None:
        query = query.filter(IntradayRsiAlert.monitor_id == monitor_id)
    alerts = query.order_by(IntradayRsiAlert.candle_timestamp.desc()).limit(limit).all()
    return [_serialize_alert(alert) for alert in alerts]
