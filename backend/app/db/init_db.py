from .session import engine
from .base_class import Base

# Import all models so SQLAlchemy registers them.
# `app.models.models` includes GreeksSnapshot and other shared models.
from app.models.instrument import Instrument
from app.models.ticks import Tick
from app.models.latest_tick import LatestTick
from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m
from app.models.symbol_load_summary import SymbolLoadSummary
from app.models.ma_signal_cache import MASignalCache
from app.models.rsi_signal_cache import RSISignalCache
from app.models.ath_signal_cache import ATHSignalCache
from app.models.history_screener import HistoryScreenerRun, HistoryScreenerResult
from app.models.backtest_conversation import BacktestConversation
from app.models.intraday_rsi_monitor import IntradayRsiMonitor, IntradayRsiAlert
from app.models import models

def init_db():
    Base.metadata.create_all(bind=engine)
