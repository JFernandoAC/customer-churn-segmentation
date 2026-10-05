"""Create the tables and load the raw CSV into Postgres."""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

CSV_PATH = Path("data/raw/online_retail_II.csv")

# Original column names -> names that are comfortable to write in SQL
COLUMN_NAMES = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}


def run_sql_file(engine, path):
    with engine.begin() as connection:
        connection.execute(text(Path(path).read_text()))


def main():
    engine = get_engine()

    print("Creating table raw_transactions...")
    run_sql_file(engine, "sql/01_create_tables.sql")

    df = pd.read_csv(CSV_PATH, dtype={"Invoice": str, "StockCode": str, "Customer ID": "Int64"},
                     parse_dates=["InvoiceDate"])
    df = df.rename(columns=COLUMN_NAMES)

    # if_exists="append" keeps the column types we defined in the SQL file.
    print(f"Loading {len(df):,} rows (takes a minute or two)...")
    df.to_sql("raw_transactions", engine, if_exists="append", index=False, chunksize=10_000)

    print("Creating views clean_transactions and cancellations...")
    run_sql_file(engine, "sql/02_clean_view.sql")

    with engine.connect() as connection:
        clean_rows = connection.execute(text("SELECT COUNT(*) FROM clean_transactions")).scalar()
    print(f"Done. clean_transactions has {clean_rows:,} rows.")


if __name__ == "__main__":
    main()
