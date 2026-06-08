import time
from datetime import datetime, timedelta
from typing import Dict, List

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.services.ingestion_engine import get_active_symbols

ALPACA_API_KEY = "PKSQADWO6NSFCZ3XOMK4RG54YA"
ALPACA_SECRET_KEY = "5fJMeiCcTt5XJ2wcNzZAnwTLTn8HbYKLy1yjXEJWWKRo"

client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

DELAYED_QUOTE_CACHE: Dict[str, dict] = {}
DEFAULT_BATCH_SIZE = 30
DEFAULT_POLL_INTERVAL_SECONDS = 15 * 60


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _chunked(symbols: List[str], size: int):
    for i in range(0, len(symbols), size):
        yield symbols[i:i + size]


def fetch_delayed_quotes(symbols: List[str]) -> Dict[str, dict]:
    symbols = [s for s in { _normalize_symbol(s) for s in symbols if s }]
    if not symbols:
        return {}

    end = datetime.utcnow()
    start = end - timedelta(minutes=45)

    request_params = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Minute,
        start=start,
        end=end,
        feed="iex"
    )

    bars = client.get_stock_bars(request_params)
    df = bars.df
    result: Dict[str, dict] = {}

    if df.empty:
        return result

    for index, row in df.iterrows():
        if isinstance(index, tuple):
            symbol, timestamp = index[0], index[1]
        else:
            symbol = symbols[0]
            timestamp = index

        quote = {
            "symbol": _normalize_symbol(symbol),
            "timestamp": timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "delayed_by_minutes": 15,
            "updated_at": datetime.utcnow(),
            "source": "alpaca_iex",
        }

        result[quote["symbol"]] = quote
        DELAYED_QUOTE_CACHE[quote["symbol"]] = quote

    return result


def get_cached_delayed_quote(symbol: str) -> dict:
    return DELAYED_QUOTE_CACHE.get(_normalize_symbol(symbol))


def get_cached_delayed_quotes(symbols: List[str]) -> List[dict]:
    symbol_list = [ _normalize_symbol(s) for s in symbols if s ]
    missing = [s for s in symbol_list if s not in DELAYED_QUOTE_CACHE]
    if missing:
        fetch_delayed_quotes(missing)

    return [DELAYED_QUOTE_CACHE[s] for s in symbol_list if s in DELAYED_QUOTE_CACHE]


def refresh_delayed_quotes(symbols: List[str]) -> Dict[str, dict]:
    quotes = {}
    for chunk in _chunked(symbols, DEFAULT_BATCH_SIZE):
        quotes.update(fetch_delayed_quotes(chunk))
        time.sleep(1)
    return quotes


def start_delayed_quote_polling(interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS):
    while True:
        symbols = get_active_symbols()
        if symbols:
            try:
                refresh_delayed_quotes(symbols)
            except Exception as exc:
                print(f"❌ Delayed quote polling error: {exc}")
        time.sleep(interval_seconds)
