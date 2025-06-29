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

def macd_strategy(df, short=12, long=26, signal=9):
    df = df.copy()
    df['EMA_short'] = df['Close'].ewm(span=short, adjust=False).mean()
    df['EMA_long'] = df['Close'].ewm(span=long, adjust=False).mean()
    df['MACD'] = df['EMA_short'] - df['EMA_long']
    df['Signal_Line'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['Signal'] = 0
    df.loc[df['MACD'] > df['Signal_Line'], 'Signal'] = 1
    df.loc[df['MACD'] < df['Signal_Line'], 'Signal'] = -1
    return df


def bollinger_strategy(df, window=20, num_std=2):
    df = df.copy()
    df['SMA'] = df['Close'].rolling(window).mean()
    df['STD'] = df['Close'].rolling(window).std()
    df['Upper'] = df['SMA'] + num_std * df['STD']
    df['Lower'] = df['SMA'] - num_std * df['STD']
    df['Signal'] = 0
    df.loc[df['Close'] < df['Lower'], 'Signal'] = 1
    df.loc[df['Close'] > df['Upper'], 'Signal'] = -1
    return df


def momentum_roc_strategy(df, period=10, upper_thresh=2, lower_thresh=-2):
    df = df.copy()
    df['ROC'] = df['Close'].pct_change(periods=period) * 100
    df['Signal'] = 0
    df.loc[df['ROC'] > upper_thresh, 'Signal'] = 1
    df.loc[df['ROC'] < lower_thresh, 'Signal'] = -1
    return df


def dual_sma_strategy(df, short_window=50, long_window=200):
    df = df.copy()
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()
    df['Signal'] = 0
    df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
    df.loc[df['SMA_Short'] < df['SMA_Long'], 'Signal'] = -1
    return df


def rsi_threshold_strategy(df, period=14, lower=30, upper=70):
    df = df.copy()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Signal'] = 0
    df.loc[df['RSI'] < lower, 'Signal'] = 1
    df.loc[df['RSI'] > upper, 'Signal'] = -1
    return df

def ema_crossover_strategy(df: pd.DataFrame, short_window=20, long_window=50) -> pd.DataFrame:
    df["EMA_short"] = df["Close"].ewm(span=short_window, adjust=False).mean()
    df["EMA_long"] = df["Close"].ewm(span=long_window, adjust=False).mean()
    df = df.dropna(subset=["EMA_short", "EMA_long"]).copy()
    df["Signal"] = (df["EMA_short"] > df["EMA_long"]).astype(int)
    return df

def rsi_sma_strategy(df: pd.DataFrame, short_window=20, long_window=50) -> pd.DataFrame:
    # Calculate RSI
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Calculate SMA
    df["MA_short"] = df["Close"].rolling(window=short_window).mean()
    df["MA_long"] = df["Close"].rolling(window=long_window).mean()

    df = df.dropna(subset=["RSI", "MA_short"]).copy()

    buy_signal = (df["RSI"] < 40) & (df["Close"] > df["MA_short"])
    sell_signal = (df["RSI"] > 70) & (df["Close"] < df["MA_short"])

    df["Signal"] = np.nan
    df.loc[buy_signal, "Signal"] = 1
    df.loc[sell_signal, "Signal"] = 0
    df["Signal"] = df["Signal"].ffill().fillna(0)

    return df
