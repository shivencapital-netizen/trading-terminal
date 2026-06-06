import pandas as pd
import requests
from app.db.session import SessionLocal
from app.models.instrument import Instrument

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

def load_sp500():
    db = SessionLocal()

    print(">>> load_sp500() STARTED")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # Fetch HTML
    print(">>> Downloading Wikipedia page...")
    response = requests.get(WIKI_URL, headers=headers)
    response.raise_for_status()

    print(">>> HTML downloaded, length:", len(response.text))

    # Try parsing tables
    try:
        print(">>> Parsing tables with pandas.read_html()...")
        tables = pd.read_html(response.text)
        print(">>> Number of tables found:", len(tables))
    except Exception as e:
        print(">>> ERROR in read_html:", e)
        raise

    # Find the correct table
    df = None
    for idx, table in enumerate(tables):
        print(f">>> Checking table {idx} with columns: {list(table.columns)}")
        if "Symbol" in table.columns:
            print(">>> Found S&P 500 table at index:", idx)
            df = table
            break

    if df is None:
        print(">>> ERROR: Could not find S&P 500 table on Wikipedia")
        raise Exception("Could not find S&P 500 table on Wikipedia")

    print(">>> Extracting symbols...")

    symbols = df["Symbol"].tolist()

    count = 0
    for sym in symbols:
        sym = sym.replace(".", "-")
        inst = Instrument(symbol=sym, active=True)
        db.merge(inst)
        count += 1

    db.commit()
    db.close()

    print(f">>> Loaded {count} S&P 500 symbols")
    return count
