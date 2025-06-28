import pandas as pd
import numpy as np

def compute_sharpe(portfolio_value, risk_free_rate=0.0):
    returns = portfolio_value.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return float("nan")
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def compute_max_drawdown(portfolio_value):
    cumulative_max = portfolio_value.cummax()
    drawdown = (portfolio_value - cumulative_max) / cumulative_max
    return abs(drawdown.min())

def calculate_metrics(portfolio_value):
    portfolio_value_clean = portfolio_value.dropna()

    total_return = float("nan")
    annual_return = float("nan")

    if len(portfolio_value_clean) >= 2:
        start_value = portfolio_value_clean.iloc[0]
        end_value = portfolio_value_clean.iloc[-1]
        num_years = (portfolio_value_clean.index[-1] - portfolio_value_clean.index[0]).days / 365.25
        total_return = (end_value / start_value) - 1
        annual_return = (1 + total_return) ** (1 / num_years) - 1

    sharpe_ratio = compute_sharpe(portfolio_value_clean)
    max_drawdown = compute_max_drawdown(portfolio_value_clean)

    return {
        "total_return": total_return * 100,
        "annual_return": annual_return * 100,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown * 100,
    }
