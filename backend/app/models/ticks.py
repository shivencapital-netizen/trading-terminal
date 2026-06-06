from sqlalchemy import Column, BigInteger, String, Float, TIMESTAMP
from sqlalchemy.sql import func
from app.db.base_class import Base


class Tick(Base):
    __tablename__ = "ticks"

    id = Column(BigInteger, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
    exchange = Column(String, nullable=True)

