from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint, Index
from app.db.base_class import Base


class MASignalCache(Base):
    __tablename__ = "ma_signal_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_date = Column(Date, nullable=False, index=True)

    fast_ma = Column(String(10), nullable=False)
    slow_ma = Column(String(10), nullable=False)
    fast_period = Column(Integer, nullable=False)
    slow_period = Column(Integer, nullable=False)
    direction = Column(String(10), nullable=False)

    open = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    prev_day_close = Column(Float, nullable=True)
    percent_change = Column(Float, nullable=True)

    fast_prev = Column(Float, nullable=True)
    fast_curr = Column(Float, nullable=True)
    slow_prev = Column(Float, nullable=True)
    slow_curr = Column(Float, nullable=True)

    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    cached_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "signal_date",
            "fast_ma",
            "slow_ma",
            "fast_period",
            "slow_period",
            "direction",
            name="uq_ma_signal_cache_unique",
        ),
        Index(
            "ix_ma_signal_cache_query",
            "signal_date",
            "fast_ma",
            "slow_ma",
            "fast_period",
            "slow_period",
            "direction",
        ),
    )
