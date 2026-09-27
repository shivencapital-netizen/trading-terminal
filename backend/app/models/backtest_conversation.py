from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.db.base_class import Base


class BacktestConversation(Base):
    __tablename__ = "backtest_conversations"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    years = Column(Integer, nullable=False)
    threshold_percent = Column(Float, nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
