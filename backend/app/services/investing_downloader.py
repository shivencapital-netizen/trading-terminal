import os
import re
import time
import requests
from datetime import datetime, timedelta

BASE_DIR = r"D:\trading_terminal\data\investing"
PARAM_FILE = os.path.join(BASE_DIR, "params.txt")
INCOMING_DIR = os.path.join(BASE_DIR, "incoming")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml",
    "Referer": "https://www.investing.com",
}

def read_params():
    symbols = []
    with open(PARAM_FILE, "r") as f:
        for line in f:
            if "|" in line:
                symbol, url = line.strip().split("|")
                symbols.append((symbol.upper(), url))
    return symbols


def extract_symbol_id(html):
    match = re.search(r"pairId:\s*(\d+)", html)
    return match.group(1) if match else None


def download_csv(symbol, url):
    print(f"⬇ Fetching page for {symbol}")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: Load the page to get cookies + token + symbol ID
    r = session.get(url)
    if r.status_code != 200:
        print(f"⚠ Failed to load page: HTTP {r.status_code}")
        return False

    symbol_id = extract_symbol_id(r.text)
    if not symbol_id:
        print(f"❌ Could not extract symbol ID for {symbol}")
        return False

    print(f"🔍 Symbol ID for {symbol}: {symbol_id}")

    # Step 2: Build POST payload
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)

    payload = {
        "curr_id": symbol_id,
        "st_date": start_date.strftime("%m/%d/%Y"),
        "end_date": end_date.strftime("%m/%d/%Y"),
        "interval_sec": "60",  # 1-minute candles
        "sort_col": "date",
        "sort_ord": "DESC",
        "action": "historical_data"
    }

    download_url = "https://www.investing.com/instruments/HistoricalDataAjax"

    print(f"⬇ Downloading CSV for {symbol}")

    r = session.post(download_url, data=payload, headers={
        **HEADERS,
        "X-Requested-With": "XMLHttpRequest"
    })

    if r.status_code != 200:
        print(f"⚠ Download failed: HTTP {r.status_code}")
        return False

    # Step 3: Save CSV
    filepath = os.path.join(INCOMING_DIR, f"{symbol}_1m.csv")
    with open(filepath, "wb") as f:
        f.write(r.content)

    print(f"✅ Saved → {filepath}")
    return True


def run_daily_download():
    symbols = read_params()
    print(f"📄 Downloading {len(symbols)} symbols...")

    for symbol, url in symbols:
        download_csv(symbol, url)
        time.sleep(2)

    print("🎯 Daily download complete.")


if __name__ == "__main__":
    run_daily_download()
