from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    routes_auth,
    routes_users,
    routes_trades,
    routes_positions,
    routes_backtest,
    routes_screener,
    routes_greeks,
    routes_admin,
    routes_charts,
    routes_instruments,
)
from app.api.v1 import routes_quotes

from app.db.init_db import init_db

import threading

# ⭐ FIXED IMPORTS — match your actual folder
from app.services.realtime_engine import start_realtime_ingestion
from app.services.ingestion_engine import candle_builder_loop
from app.services.delayed_data import start_delayed_quote_polling


app = FastAPI(
    title="Trading Terminal Backend",
    description="Local-only backend for private trading terminal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(routes_users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(routes_trades.router, prefix="/api/v1/trades", tags=["Trades"])
app.include_router(routes_positions.router, prefix="/api/v1/positions", tags=["Positions"])
app.include_router(routes_backtest.router, prefix="/api/v1/backtest", tags=["Backtesting"])
app.include_router(routes_screener.router, prefix="/api/v1/screener", tags=["Screener"])
app.include_router(routes_greeks.router, prefix="/api/v1/greeks", tags=["Greeks"])
app.include_router(routes_admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(routes_charts.router, prefix="/api/v1/charts", tags=["Charts"])
app.include_router(routes_instruments.router, prefix="/api/v1/instruments", tags=["Instruments"])
app.include_router(routes_quotes.router, prefix="/api/v1/quotes", tags=["Delayed Quotes"])


@app.on_event("startup")
async def startup_event():
    print("🚀 Starting Trading Terminal Backend...")
    init_db()
    print("📦 Database initialized.")
    print("🟢 Backend is ready.")

    # Start real-time tick ingestion
    threading.Thread(target=start_realtime_ingestion, daemon=True).start()
    print("⚡ Real-time ingestion engine thread started.")

    # Start 1-minute candle builder
    threading.Thread(target=candle_builder_loop, daemon=True).start()
    print("🕒 Candle builder loop started.")

    # Start free delayed-data polling (15-minute delayed IEX bars)
    threading.Thread(target=start_delayed_quote_polling, daemon=True).start()
    print("⏱️  Delayed quote polling thread started.")


@app.get("/")
def root():
    return {"message": "Trading Terminal Backend Running Locally"}
