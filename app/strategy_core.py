# app/strategy_core.py

import pandas as pd

def sma_crossover_strategy(data: pd.DataFrame, short_window: int = 50, long_window: int = 200):
    df = data.copy()
    df["SMA_Short"] = df["Close"].rolling(window=short_window).mean()
    df["SMA_Long"] = df["Close"].rolling(window=long_window).mean()

    df["Signal"] = 0
    condition = df["SMA_Short"] > df["SMA_Long"]
    df.loc[condition, "Signal"] = 1
    df.loc[~condition, "Signal"] = -1

    return df
