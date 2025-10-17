-- Create stocks table
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    target REAL NOT NULL,
    direction TEXT CHECK(direction IN ('above','below')) NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    target REAL NOT NULL,
    direction TEXT NOT NULL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create latest_prices table
CREATE TABLE IF NOT EXISTS latest_prices (
    symbol TEXT PRIMARY KEY,
    price REAL,
    high REAL,
    low REAL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    symbol TEXT PRIMARY KEY,
    pred_next REAL,
    src_days INTEGER,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_enabled ON stocks(enabled);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts);
CREATE INDEX IF NOT EXISTS idx_latest_prices_ts ON latest_prices(ts);
CREATE INDEX IF NOT EXISTS idx_predictions_ts ON predictions(ts);