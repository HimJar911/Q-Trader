# app/backtester.py

import pandas as pd

def backtest_strategy(df: pd.DataFrame, initial_cash: float = 10_000):
    df = df.copy()

    # Forward fill 1/-1 signals, treat 0 as no new signal
    df["Position"] = df["Signal"].replace(0, pd.NA).ffill()
    df["Position"] = df["Position"].fillna(0)

    # Calculate daily return and strategy return
    df["Market Return"] = df["Close"].pct_change()
    df["Strategy Return"] = df["Market Return"] * df["Position"].shift(1)

    # Portfolio value over time
    df["Portfolio Value"] = (1 + df["Strategy Return"]).cumprod() * initial_cash

    return df
