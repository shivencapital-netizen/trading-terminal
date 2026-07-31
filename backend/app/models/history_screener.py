from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class HistoryScreenerRun(Base):
    __tablename__ = "history_screener_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="History Screener Scan")
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    results = relationship(
        "HistoryScreenerResult",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class HistoryScreenerResult(Base):
    __tablename__ = "history_screener_results"

    id = Column(Integer, primary_key=True, index=True)
    history_screener_run_id = Column(
        Integer,
        ForeignKey("history_screener_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol = Column(String(20), index=True, nullable=False)
    scan_date = Column(DateTime(timezone=True), nullable=False, index=True)
    last_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    vwap = Column(Float, nullable=False)
    percent_change = Column(Float, nullable=False)
    score = Column(Float, nullable=True)
    data = Column(JSON, nullable=True)
    sparkline = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run = relationship("HistoryScreenerRun", back_populates="results")

    __table_args__ = (
        Index("ix_history_screener_symbol_date", "symbol", "scan_date"),
    )
