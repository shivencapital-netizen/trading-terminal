from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, Index
from app.db.base_class import Base


class RSISignalCache(Base):
    __tablename__ = "rsi_signal_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_date = Column(Date, nullable=False, index=True)

    rsi_period = Column(Integer, nullable=False)
    rsi_level = Column(Float, nullable=False)
    direction = Column(String(10), nullable=False)

    open = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    prev_day_close = Column(Float, nullable=True)
    percent_change = Column(Float, nullable=True)

    rsi_prev = Column(Float, nullable=True)
    rsi_curr = Column(Float, nullable=True)

    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    cached_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "signal_date",
            "rsi_period",
            "rsi_level",
            "direction",
            name="uq_rsi_signal_cache_unique",
        ),
        Index(
            "ix_rsi_signal_cache_query",
            "signal_date",
            "rsi_period",
            "rsi_level",
            "direction",
        ),
    )
