import asyncio
import json
import websockets
from datetime import datetime

from app.db.session import SessionLocal
from app.services.ingestion_engine import ingest_tick, get_active_symbols

ALPACA_API_KEY = "PKSQADWO6NSFCZ3XOMK4RG54YA"
ALPACA_SECRET_KEY = "5fJMeiCcTt5XJ2wcNzZAnwTLTn8HbYKLy1yjXEJWWKRo"

# SIP feed (paid). If using free tier, switch to IEX:
ALPACA_WS_URL = "wss://stream.data.alpaca.markets/v2/iex"

MAX_SYMBOLS_PER_BATCH = 25   # safe for free tier


async def subscribe_in_batches(ws, symbols):
    """Subscribe to symbols in safe batches."""
    for i in range(0, len(symbols), MAX_SYMBOLS_PER_BATCH):
        batch = symbols[i:i + MAX_SYMBOLS_PER_BATCH]
        await ws.send(json.dumps({
            "action": "subscribe",
            "trades": batch
        }))
        print(f"📡 Subscribed batch: {batch}")
        await asyncio.sleep(0.5)  # avoid rate limits


async def alpaca_ws_loop():
    while True:
        try:
            print("🔌 Connecting to Alpaca WebSocket...")
            async with websockets.connect(ALPACA_WS_URL, ping_interval=20, ping_timeout=20) as ws:

                # Authenticate
                await ws.send(json.dumps({
                    "action": "auth",
                    "key": ALPACA_API_KEY,
                    "secret": ALPACA_SECRET_KEY
                }))
                print("🔐 Auth Response:", await ws.recv())

                # Get symbols from DB
                symbols = get_active_symbols()
                print(f"📡 Total symbols: {len(symbols)}")

                # Subscribe in batches
                await subscribe_in_batches(ws, symbols)

                # Main loop
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    for event in data:
                        if event.get("T") == "t":  # trade tick
                            db = SessionLocal()
                            ingest_tick(
                                db=db,
                                symbol=event["S"],
                                price=event["p"],
                                volume=event["s"],
                                exchange=event.get("x")
                            )
                            db.close()

        except Exception as e:
            print("❌ WebSocket error:", e)
            print("🔁 Reconnecting in 3 seconds...")
            await asyncio.sleep(3)


def start_realtime_ingestion():
    asyncio.run(alpaca_ws_loop())
