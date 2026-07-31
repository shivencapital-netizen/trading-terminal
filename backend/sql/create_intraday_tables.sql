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
ADD COLUMN IF NOT EXISTS tick_size DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS last_loaded_time TIMESTAMP WITH TIME ZONE;

CREATE TABLE IF NOT EXISTS symbol_load_summary (
    symbol TEXT PRIMARY KEY,
    candle_count INT NOT NULL DEFAULT 0,
    last_loaded_time TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_symbol_load_summary_updated_at
    ON symbol_load_summary(updated_at);

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
