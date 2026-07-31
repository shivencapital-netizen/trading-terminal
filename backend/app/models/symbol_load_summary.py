from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base


class SymbolLoadSummary(Base):
    __tablename__ = "symbol_load_summary"

    symbol = Column(String(20), primary_key=True, index=True, nullable=False)
    candle_count = Column(Integer, nullable=False, default=0)
    last_loaded_time = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
