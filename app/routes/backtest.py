from fastapi import APIRouter, Query, HTTPException
import yfinance as yf
import pandas as pd
from app.strategies.moving_average import moving_average_strategy
from app.performance_metrics import calculate_metrics

router = APIRouter()

@router.get("/backtest")
def run_backtest(
    symbol: str = Query(...),
    start: str = Query(...),
    end: str = Query(...),
    short_window: int = 20,
    long_window: int = 50
):
    try:
        print(f"\n🟢 Starting backtest for {symbol} from {start} to {end}")
        data = yf.download(symbol, start=start, end=end)

        # 🛠️ Flatten MultiIndex column like ('Close', 'AAPL') → 'Close'
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        print(f"📊 Data shape: {data.shape}")
        print(f"📊 Columns: {data.columns.tolist()}")

        if data.empty or 'Close' not in data.columns:
            raise ValueError("No data available for this symbol or date range.")

        signals = moving_average_strategy(data, short_window, long_window)

        initial_capital = 10000

        # Positions and returns must both be 1D Series
        positions = signals['signal'].shift(1).fillna(0)
        returns = data['Close'].pct_change().fillna(0)

        # Confirm types and dimensions
        if isinstance(positions, pd.DataFrame):
            positions = positions.iloc[:, 0]
        if isinstance(returns, pd.DataFrame):
            returns = returns.iloc[:, 0]

        portfolio_returns = positions * returns
        portfolio_value = initial_capital * (1 + portfolio_returns.cumsum())

        # Final 1D Series
        portfolio_series = pd.Series(portfolio_value.values, index=data.index)

        metrics = calculate_metrics(portfolio_series)

        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "strategy": "moving_average",
            "metrics": metrics
        }

    except Exception as e:
        print("❌ Exception:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
