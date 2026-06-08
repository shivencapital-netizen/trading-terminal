import argparse
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.services.history_loader import load_history_1m


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load S&P 500 historical 1-minute candles into candles_1m."
    )

    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Total number of years to load going back from today.",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Single symbol to load instead of all instruments.",
    )
    parser.add_argument(
        "--year-step",
        type=int,
        default=1,
        help="Window size in years for each load pass. Use 1 for one year at a time.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of symbols loaded from the instruments table.",
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
    symbols = [s.upper() for s in symbols if s.upper() not in [x.upper() for x in skip_symbols]]

    if not symbols:
        raise RuntimeError(
            "No symbols found in instruments table. Run the S&P 500 loader first."
        )

    return symbols


def build_year_windows(years: int, year_step: int):
    now = datetime.combine(datetime.today().date(), datetime.min.time())
    windows = []

    for offset in range(0, years, year_step):
        end = now - timedelta(days=365 * offset)
        start = end - timedelta(days=365 * year_step)
        windows.append((start, end))

    return windows


def main():
    args = parse_args()
    db = SessionLocal()

    try:
        symbols = get_symbols(db, args.symbol, args.limit, args.skip_symbols)
        windows = build_year_windows(args.years, args.year_step)

        print(f"Loaded {len(symbols)} symbols")
        print(f"Loading {args.years} years in {len(windows)} window(s) of {args.year_step} year(s) each")

        for symbol in symbols:
            print(f"\n=== Symbol: {symbol} ===")
            for idx, (start, end) in enumerate(windows, start=1):
                print(
                    f"[{idx}/{len(windows)}] Loading {symbol} from {start.date()} to {end.date()}"
                )
                inserted = load_history_1m(
                    db,
                    symbol,
                    start=start,
                    end=end,
                )
                print(f"Inserted {inserted} rows for {symbol} ({start.date()} → {end.date()})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
