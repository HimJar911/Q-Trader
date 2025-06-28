import pandas as pd

def moving_average_strategy(data: pd.DataFrame, short_window=20, long_window=50):
    """
    Moving average crossover strategy with safe logic.
    """
    if 'Close' not in data.columns:
        raise ValueError("Input data must contain a 'Close' column.")

    signals = pd.DataFrame(index=data.index)
    signals['price'] = data['Close']
    signals['short_ma'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
    signals['long_ma'] = data['Close'].rolling(window=long_window, min_periods=1).mean()

    # Create signal: 1 when short_ma > long_ma, else 0 — guarantee it's 1D
    raw_signal = (signals['short_ma'] > signals['long_ma']).astype(int)
    signals['signal'] = pd.Series(raw_signal.values, index=data.index)

    signals['positions'] = signals['signal'].diff().fillna(0)

    return signals
