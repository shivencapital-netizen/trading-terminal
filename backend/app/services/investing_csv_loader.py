import os
import shutil
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models.candles_1m import Candle1m
from app.db.session import SessionLocal

BASE_DIR = r"D:\trading_terminal\data\investing"
INCOMING_DIR = os.path.join(BASE_DIR, "incoming")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")
PARAM_FILE = os.path.join(BASE_DIR, "params.txt")


def read_params():
    years = 1
    truncate = False
    symbols = []

    with open(PARAM_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("YEARS="):
                years = int(line.split("=")[1])
            elif line.startswith("TRUNCATE="):
                truncate = line.split("=")[1].upper() == "YES"
            else:
                symbols.append(line.upper())

    return years, truncate, symbols


def parse_investing_datetime(row):
    dt_str = f"{row['Date']} {row['Time']}"
    return datetime.strptime(dt_str, "%m/%d/%Y %H:%M:%S")


def load_csv(db: Session, filepath: str, symbol: str) -> int:
    print(f"📥 Loading CSV for {symbol}: {filepath}")

    df = pd.read_csv(filepath)

    required = ["Date", "Time", "Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            print(f"⚠ Missing column {col} in {filepath}")
            return 0

    inserted = 0

    for _, row in df.iterrows():
        ts = parse_investing_datetime(row).replace(tzinfo=None)

        exists = (
            db.query(Candle1m)
            .filter(Candle1m.symbol == symbol)
            .filter(Candle1m.start_time == ts)
            .first()
        )
        if exists:
            continue

        candle = Candle1m(
            symbol=symbol,
            start_time=ts,
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(str(row["Volume"]).replace(",", "")),
        )

        db.add(candle)
        inserted += 1

    db.commit()
    print(f"✅ Inserted {inserted} candles for {symbol}")
    return inserted


def archive_file(filepath: str):
    filename = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archived_name = f"{filename.replace('.csv', '')}_{timestamp}.csv"
    archived_path = os.path.join(ARCHIVE_DIR, archived_name)

    shutil.move(filepath, archived_path)
    print(f"📦 Archived → {archived_path}")


def refresh_all():
    years, truncate, symbols = read_params()

    print(f"📄 Params Loaded → YEARS={years}, TRUNCATE={truncate}, SYMBOLS={symbols}")

    db = SessionLocal()

    if truncate:
        print("⚠ Truncating candles_1m table...")
        db.query(Candle1m).delete()
        db.commit()
        print("🧹 Table truncated.")

    total = 0

    for symbol in symbols:
        filename = f"{symbol}_1m.csv"
        filepath = os.path.join(INCOMING_DIR, filename)

        if not os.path.exists(filepath):
            print(f"⚠ CSV not found for {symbol}: {filepath}")
            continue

        inserted = load_csv(db, filepath, symbol)
        total += inserted

        archive_file(filepath)

    print(f"🎯 Total inserted across all symbols: {total}")
    db.close()


if __name__ == "__main__":
    refresh_all()
