CREATE TABLE IF NOT EXISTS history_screener_results (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    scan_date TIMESTAMP WITH TIME ZONE NOT NULL,
    last_price DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    vwap DOUBLE PRECISION NOT NULL,
    percent_change DOUBLE PRECISION NOT NULL,
    score DOUBLE PRECISION,
    data JSONB,
    sparkline JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_history_screener_symbol_date ON history_screener_results(symbol, scan_date);
