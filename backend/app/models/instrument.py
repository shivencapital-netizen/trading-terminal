from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    exchange = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_loaded_time = Column(TIMESTAMP(timezone=True), nullable=True)

    orders = relationship("Order", back_populates="instrument")
    trades = relationship("Trade", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    greeks_snapshots = relationship("GreeksSnapshot", back_populates="instrument")
    screener_results = relationship("ScreenerResult", back_populates="instrument")


