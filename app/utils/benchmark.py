import yfinance as yf
import pandas as pd

def fetch_benchmark(symbol="SPY", start="2020-01-01", end="2024-01-01"):
    df = yf.download(symbol, start=start, end=end)
    df = df[['Close']].copy()
    df.rename(columns={"Close": "Benchmark"}, inplace=True)
    df.dropna(inplace=True)
    return df
