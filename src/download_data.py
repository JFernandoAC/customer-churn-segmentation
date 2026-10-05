"""Download the Online Retail II dataset from UCI and save it as one CSV."""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
RAW_DIR = Path("data/raw")
EXCEL_PATH = RAW_DIR / "online_retail_II.xlsx"
CSV_PATH = RAW_DIR / "online_retail_II.csv"


def download_excel():
    if EXCEL_PATH.exists():
        print("Excel already downloaded, skipping.")
        return
    print("Downloading dataset (~45 MB)...")
    response = requests.get(URL, timeout=300)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        zip_file.extractall(RAW_DIR)


def excel_to_csv():
    # The Excel file has one sheet per year. sheet_name=None reads all of them.
    print("Reading Excel (this takes a few minutes)...")
    sheets = pd.read_excel(EXCEL_PATH, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
    df = pd.concat(sheets.values(), ignore_index=True)

    # Both sheets contain 1-9 Dec 2010, so those rows appear twice. The file
    # also has some lines repeated by mistake inside the same invoice.
    rows_before = len(df)
    df = df.drop_duplicates()
    print(f"Removed {rows_before - len(df):,} duplicated rows.")

    # Customer ID is read as float (1234.0) because of the empty values.
    df["Customer ID"] = df["Customer ID"].astype("Int64")
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved {len(df):,} rows to {CSV_PATH}")


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    download_excel()
    excel_to_csv()
