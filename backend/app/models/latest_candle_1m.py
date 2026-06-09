from sqlalchemy import Column, String, Float, BigInteger, DateTime
from app.db.base_class import Base


class LatestCandle1m(Base):
    __tablename__ = "latest_candles_1m"

    symbol = Column(String(20), primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
