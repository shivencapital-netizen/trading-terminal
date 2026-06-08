import argparse

from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.services.history_loader import load_history_1m_delta


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load incremental 1-minute candle delta from Alpaca into candles_1m."
    )
    parser.add_argument(
        "--years",
        type=int,
        default=1,
        help="Backfill years when no existing candle data is available.",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Single symbol to load instead of all instruments.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of instruments to load.",
    )
    parser.add_argument(
        "--skip-symbols",
        nargs="*",
        default=[],
        help="Symbols to skip when loading all instruments.",
    )
    return parser.parse_args()


def get_symbols(db, symbol: str | None, limit: int | None, skip_symbols: list[str]):
    if symbol:
        return [symbol.upper()]

    query = db.query(Instrument).order_by(Instrument.symbol)
    if limit:
        query = query.limit(limit)

    symbols = [row.symbol for row in query.all() if row.symbol]
    skip_upper = {s.upper() for s in skip_symbols}
    symbols = [s.upper() for s in symbols if s.upper() not in skip_upper]

    if not symbols:
        raise RuntimeError(
            "No symbols found in instruments table. Run the instrument loader first."
        )

    return symbols


def main():
    args = parse_args()
    db = SessionLocal()

    try:
        symbols = get_symbols(db, args.symbol, args.limit, args.skip_symbols)
        print(f"Loaded {len(symbols)} symbols for incremental delta load")

        total_inserted = 0
        for symbol in symbols:
            print(f"\n=== Loading delta for {symbol} ===")
            inserted = load_history_1m_delta(db, symbol, args.years)
            print(f"Inserted {inserted} new rows for {symbol}")
            total_inserted += inserted

        print(f"\n🎯 Total inserted across all symbols: {total_inserted}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
