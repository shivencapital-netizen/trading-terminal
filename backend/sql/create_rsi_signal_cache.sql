CREATE TABLE IF NOT EXISTS rsi_signal_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_date DATE NOT NULL,
    rsi_period INTEGER NOT NULL,
    rsi_level DOUBLE PRECISION NOT NULL,
    direction VARCHAR(10) NOT NULL,
    open DOUBLE PRECISION,
    last_price DOUBLE PRECISION,
    prev_day_close DOUBLE PRECISION,
    percent_change DOUBLE PRECISION,
    rsi_prev DOUBLE PRECISION,
    rsi_curr DOUBLE PRECISION,
    source_updated_at TIMESTAMP WITH TIME ZONE,
    cached_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_rsi_signal_cache_unique
    ON rsi_signal_cache(symbol, signal_date, rsi_period, rsi_level, direction);

CREATE INDEX IF NOT EXISTS ix_rsi_signal_cache_query
    ON rsi_signal_cache(signal_date, rsi_period, rsi_level, direction);

CREATE INDEX IF NOT EXISTS ix_rsi_signal_cache_symbol
    ON rsi_signal_cache(symbol);
