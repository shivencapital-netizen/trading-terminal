CREATE TABLE IF NOT EXISTS intraday_candles (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    timeframe TEXT NOT NULL DEFAULT '1m'
);

CREATE INDEX IF NOT EXISTS idx_intraday_symbol_time
    ON intraday_candles(symbol, timestamp);

CREATE INDEX IF NOT EXISTS idx_intraday_timeframe
    ON intraday_candles(timeframe);


ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS sector TEXT,
ADD COLUMN IF NOT EXISTS industry TEXT,
ADD COLUMN IF NOT EXISTS lot_size INT,
ADD COLUMN IF NOT EXISTS tick_size DOUBLE PRECISION;


CREATE TABLE IF NOT EXISTS screener_results (
    symbol TEXT PRIMARY KEY,
    last_price DOUBLE PRECISION,
    day_high DOUBLE PRECISION,
    day_low DOUBLE PRECISION,
    prev_close DOUBLE PRECISION,
    volume BIGINT,
    percent_change DOUBLE PRECISION,
    sparkline JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);
