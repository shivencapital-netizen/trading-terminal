# app/models/candles_1m.py
from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, UniqueConstraint, Index
from app.db.base_class import Base

class Candle1m(Base):
    __tablename__ = "candles_1m"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "start_time", name="uq_candles_1m_symbol_time"),
        Index("idx_candles_1m_symbol_time", "symbol", "start_time"),
    )
