# app/data_loader.py

import yfinance as yf
import pandas as pd
import os

def fetch_price_data(ticker: str, start: str = "2015-01-01", end: str = "2024-12-31") -> pd.DataFrame:
    os.makedirs("app/data_cache", exist_ok=True)
    cache_path = f"app/data_cache/{ticker}_{start}_{end}.csv"

    try:
        return pd.read_csv(cache_path, index_col="Date", parse_dates=True)
    except Exception as e:
        print(f"[WARN] Cache load failed — redownloading. Reason: {e}")
        data = yf.download(ticker, start=start, end=end, auto_adjust=False)
        data.to_csv(cache_path, index_label="Date")
        return data

