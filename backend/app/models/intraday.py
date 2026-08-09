from sqlalchemy import Column, Integer, String, Float, BigInteger, TIMESTAMP, JSON
from app.db.base_class import Base

class IntradayCandle(Base):
    __tablename__ = "intraday_candles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(TIMESTAMP, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)
    timeframe = Column(String, default="1m")
