import yfinance as yf
from datetime import datetime

# -----------------------------
#  YOUR TOP 300 SYMBOL LIST
# -----------------------------
SYMBOLS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","BRK-B","LLY","TSLA",
    "AVGO","JPM","V","UNH","XOM","WMT","MA","JNJ","PG","HD",
    "COST","BAC","MRK","ABBV","CVX","PEP","KO","ADBE","ORCL","NFLX",
    "TMO","LIN","ACN","MCD","ABT","WFC","DHR","CSCO","CRM","TXN",
    "PM","INTC","VZ","UPS","NEE","IBM","UNP","HON","QCOM","AMGN",
    "LOW","CAT","MS","GS","SPGI","RTX","BLK","AMD","SCHW","AMAT",
    "GE","MDT","ISRG","BKNG","SBUX","PLD","DE","LMT","ELV","T",
    "NOW","ADI","MO","SYK","CI","MDLZ","CB","MMC","REGN","GILD",
    "C","ADP","PFE","VRTX","CL","ZTS","CSX","BDX","MU","PANW",
    "FDX","SO","EQIX","ICE","ITW","SLB","APD","GM","USB","SHW",
    "TJX","NSC","WM","GD","AON","DUK","PNC","TGT","FIS","HCA",
    "EOG","ADSK","MAR","LRCX","AIG","PGR","MPC","KLAC","FISV","ETN",
    "PH","CME","HUM","AEP","ROP","NXPI","TRV","KDP","PSA","AZO",
    "D","MCO","AFL","OXY","CTAS","SRE","MSCI","KMB","HLT","PAYX",
    "CMCSA","DG","ORLY","CNC","IDXX","FTNT","LHX","TEL","PCAR","MNST",
    "ALL","KMI","NOC","EXC","A","ROST","VLO","PRU","GPN","DLR",
    "HPQ","SYY","ED","MET","HES","BMY","KR","PPG","AEE","DHI",
    "LEN","WMB","ECL","STZ","MCK","CDNS","CTSH","ADM","ILMN","TT",
    "OTIS","RSG","F","KHC","BKR","GLW","VRSK","MTB","WELL","PEG",
    "XEL","ALB","DLTR","HIG","KEYS","VICI","ODFL","WBA","LUV","ZBH",
    "DTE","ES","PPL","AAL","DAL","UAL","CCL","RCL","NCLH","MGM",
    "LVS","WYNN","EXPE","EBAY","BK","STT","FITB","RF","HBAN","KEY",
    "CFG","ALLY","COF","DFS","SYF","VTRS","BIIB","MRNA","BAX","EW",
    "ALGN","STE","MTD","RMD","WST","PKI","HSY","K","GIS","CPB"
]

# -----------------------------
#  EXCHANGE MAPPING
# -----------------------------
EXCHANGE_MAP = {
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NYQ": "NYSE",
    "NYS": "NYSE"
}

# -----------------------------
#  ESCAPE SQL STRINGS
# -----------------------------
def esc(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

# -----------------------------
#  GENERATE SQL ROWS
# -----------------------------
rows = []

for sym in SYMBOLS:
    yf_sym = sym.replace("BRK-B", "BRK-B")  # yfinance handles this fine
    info = yf.Ticker(yf_sym).info

    name = info.get("longName") or info.get("shortName")
    exch_raw = info.get("exchange")
    exchange = EXCHANGE_MAP.get(exch_raw, exch_raw)

    sector = info.get("sector")
    industry = info.get("industry")

    lot_size = 1
    tick_size = 0.01
    created_at = "NULL"

    row = f"({esc(sym)}, {esc(name)}, {esc(exchange)}, {esc(sector)}, {esc(industry)}, {lot_size}, {tick_size}, {created_at})"
    rows.append(row)

# -----------------------------
#  FINAL SQL OUTPUT
# -----------------------------
sql = (
    "INSERT INTO instruments (symbol, name, exchange, sector, industry, lot_size, tick_size, created_at)\n"
    "VALUES\n" +
    ",\n".join(rows) +
    ";\n"
)

with open("instruments_top300.sql", "w", encoding="utf-8") as f:
    f.write(sql)

print("Generated instruments_top300.sql successfully.")
