from sqlalchemy import Column, String, Float, Integer, DateTime
from app.db.base_class import Base

class LatestTick(Base):
    __tablename__ = "latest_ticks"

    symbol = Column(String, primary_key=True, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False)
