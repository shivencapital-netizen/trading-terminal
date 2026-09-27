from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint

from app.db.base_class import Base


class IntradayRsiMonitor(Base):
    __tablename__ = "intraday_rsi_monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    symbols = Column(JSON, nullable=False)
    rsi_period = Column(Integer, nullable=False, default=14)
    rsi_level = Column(Float, nullable=False, default=59)
    direction = Column(String(10), nullable=False, default="both")
    sms_enabled = Column(Boolean, nullable=False, default=False)
    sms_phone = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    last_checked_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntradayRsiAlert(Base):
    __tablename__ = "intraday_rsi_alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)
    rsi_period = Column(Integer, nullable=False)
    rsi_level = Column(Float, nullable=False)
    rsi_previous = Column(Float, nullable=False)
    rsi_current = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    candle_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint(
            "monitor_id",
            "symbol",
            "direction",
            "candle_timestamp",
            name="uq_intraday_rsi_alert_event",
        ),
    )
