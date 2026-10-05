-- One row per invoice line, exactly as it comes in the source file.
DROP TABLE IF EXISTS raw_transactions CASCADE;

CREATE TABLE raw_transactions (
    invoice      TEXT,
    stock_code   TEXT,
    description  TEXT,
    quantity     INTEGER,
    invoice_date TIMESTAMP,
    price        DOUBLE PRECISION,
    customer_id  INTEGER,
    country      TEXT
);

CREATE INDEX idx_raw_customer ON raw_transactions (customer_id);
CREATE INDEX idx_raw_date ON raw_transactions (invoice_date);
