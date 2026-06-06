from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Enum as SAEnum,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------
class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    PARTIALLY_FILFILLED = "PARTIALLY_FILFILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BacktestStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BrokerType(str, Enum):
    ROBINHOOD = "ROBINHOOD"
    ALPACA = "ALPACA"
    IBKR = "IBKR"
    PAPER = "PAPER"


# ---------------------------------------------------------
# User
# ---------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    broker_credentials = relationship(
        "BrokerCredential", back_populates="user", cascade="all, delete-orphan"
    )
    trades = relationship("Trade", back_populates="user")
    positions = relationship("Position", back_populates="user")
    orders = relationship("Order", back_populates="user")
    backtests = relationship("Backtest", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


# ---------------------------------------------------------
# Instruments (stocks, options, futures, etc.)
# ---------------------------------------------------------
class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), index=True, nullable=False)
    name = Column(String(255), nullable=True)
    asset_type = Column(String(50), nullable=False)  # STOCK, OPTION, FUTURE, ETF, etc.
    exchange = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    tick_size = Column(Float, nullable=True)
    lot_size = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    trades = relationship("Trade", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    orders = relationship("Order", back_populates="instrument")
    greeks_snapshots = relationship("GreeksSnapshot", back_populates="instrument")
    screener_results = relationship("ScreenerResult", back_populates="instrument")

    __table_args__ = (
        UniqueConstraint("symbol", "asset_type", name="uq_instrument_symbol_asset_type"),
    )


# ---------------------------------------------------------
# Strategies
# ---------------------------------------------------------
class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Optional: JSON config for parameters
    config = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    trades = relationship("Trade", back_populates="strategy")
    backtests = relationship("Backtest", back_populates="strategy")


# ---------------------------------------------------------
# Orders (live & simulated)
# ---------------------------------------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)

    broker_type = Column(SAEnum(BrokerType), nullable=False)
    broker_order_id = Column(String(255), nullable=True, index=True)

    side = Column(SAEnum(OrderSide), nullable=False)
    order_type = Column(SAEnum(OrderType), nullable=False)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.NEW, nullable=False)

    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0, nullable=False)

    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)

    time_in_force = Column(String(50), default="DAY", nullable=False)

    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    filled_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    raw_response = Column(JSON, nullable=True)

    user = relationship("User", back_populates="orders")
    instrument = relationship("Instrument", back_populates="orders")

    __table_args__ = (
        Index("ix_orders_user_id_status", "user_id", "status"),
    )


# ---------------------------------------------------------
# Trades (executions)
# ---------------------------------------------------------
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    broker_type = Column(SAEnum(BrokerType), nullable=False)
    broker_trade_id = Column(String(255), nullable=True, index=True)

    side = Column(SAEnum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)

    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="trades")
    instrument = relationship("Instrument", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    order = relationship("Order")

    __table_args__ = (
        Index("ix_trades_user_id_executed_at", "user_id", "executed_at"),
    )


# ---------------------------------------------------------
# Positions
# ---------------------------------------------------------
class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)

    side = Column(SAEnum(PositionSide), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)

    realized_pnl = Column(Float, default=0.0, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    last_price = Column(Float, nullable=True)

    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("user_id", "instrument_id", "side", name="uq_position_user_instrument_side"),
    )


# ---------------------------------------------------------
# Backtests
# ---------------------------------------------------------
class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)

    name = Column(String(255), nullable=False)
    status = Column(SAEnum(BacktestStatus), default=BacktestStatus.CREATED, nullable=False)

    # JSON config: symbol list, date range, capital, etc.
    config = Column(JSON, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    results = relationship(
        "BacktestResult", back_populates="backtest", cascade="all, delete-orphan"
    )


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False)

    # Aggregated metrics
    total_return = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)

    # Equity curve, per-trade stats, etc.
    metrics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    backtest = relationship("Backtest", back_populates="results")


# ---------------------------------------------------------
# Screeners
# ---------------------------------------------------------
class ScreenerRun(Base):
    __tablename__ = "screener_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # JSON config: filters, universe, timeframes, etc.
    config = Column(JSON, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    results = relationship(
        "ScreenerResult", back_populates="screener_run", cascade="all, delete-orphan"
    )


class ScreenerResult(Base):
    __tablename__ = "screener_results"

    id = Column(Integer, primary_key=True, index=True)
    screener_run_id = Column(Integer, ForeignKey("screener_runs.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)

    score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)

    # Any extra data (indicators, signals, etc.)
    data = Column(JSON, nullable=True)

    screener_run = relationship("ScreenerRun", back_populates="results")
    instrument = relationship("Instrument", back_populates="screener_results")

    __table_args__ = (
        Index("ix_screener_results_run_rank", "screener_run_id", "rank"),
    )


# ---------------------------------------------------------
# Greeks snapshots (for options)
# ---------------------------------------------------------
class GreeksSnapshot(Base):
    __tablename__ = "greeks_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)

    delta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    theta = Column(Float, nullable=True)
    vega = Column(Float, nullable=True)
    rho = Column(Float, nullable=True)

    implied_vol = Column(Float, nullable=True)
    underlying_price = Column(Float, nullable=True)

    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instrument = relationship("Instrument", back_populates="greeks_snapshots")

    __table_args__ = (
        Index("ix_greeks_instrument_snapshot", "instrument_id", "snapshot_at"),
    )


# ---------------------------------------------------------
# API keys (for your own app, not brokers)
# ---------------------------------------------------------
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False)  # store hash, not raw key
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_api_key_user_name"),
    )


# ---------------------------------------------------------
# Broker credentials (Robinhood, etc.)
# ---------------------------------------------------------
class BrokerCredential(Base):
    __tablename__ = "broker_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    broker_type = Column(SAEnum(BrokerType), nullable=False)
    # Encrypted JSON blob: tokens, refresh tokens, etc.
    credentials_encrypted = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="broker_credentials")

    __table_args__ = (
        UniqueConstraint("user_id", "broker_type", name="uq_broker_credential_user_broker"),
    )


# ---------------------------------------------------------
# Application settings
# ---------------------------------------------------------
class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ---------------------------------------------------------
# Audit logs
# ---------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_created_at", "user_id", "created_at"),
    )


# ---------------------------------------------------------
# Error logs
# ---------------------------------------------------------
class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50), nullable=False)  # ERROR, WARNING, INFO, etc.
    message = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_error_logs_level_created_at", "level", "created_at"),
    )
