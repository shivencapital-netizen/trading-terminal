from .session import engine
from .base_class import Base

# Import all models so SQLAlchemy registers them
from app.models.instrument import Instrument
from app.models.ticks import Tick
from app.models.latest_tick import LatestTick
from app.models.candles_1m import Candle1m
from app.models.latest_candle_1m import LatestCandle1m

def init_db():
    Base.metadata.create_all(bind=engine)
