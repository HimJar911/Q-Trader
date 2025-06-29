# ------------- app/routes/backtest.py (UPDATED WITH SPY BENCHMARK) -------------

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import traceback
from app.utils.benchmark import fetch_benchmark
from app.routes.metrics import compare_strategy_vs_benchmark

router = APIRouter()

@router.get("/backtest")
def backtest(
    symbol: str,
    start: str,
    end: str,
    short_window: int = Query(...),
    long_window: int = Query(...),
    strategy: str = Query("sma")
):
    try:
        df = yf.download(symbol, start=start, end=end)
        df.columns = df.columns.get_level_values(0)
        df = df.reset_index()

        # Benchmark SPY
        spy_df = yf.download("SPY", start=start, end=end)
        spy_df.columns = spy_df.columns.get_level_values(0)
        spy_df = spy_df.reset_index()
        spy_df["Returns"] = spy_df["Close"].pct_change().fillna(0)
        spy_df["Equity"] = (1 + spy_df["Returns"]).cumprod() * 100000
        spy_df = spy_df[["Date", "Equity"]].rename(columns={"Equity": "benchmark_equity"})
        spy_df["Date"] = pd.to_datetime(spy_df["Date"])

        if strategy.lower() == "ema":
            df["MA_short"] = df["Close"].ewm(span=short_window, adjust=False).mean()
            df["MA_long"] = df["Close"].ewm(span=long_window, adjust=False).mean()
        else:
            df["MA_short"] = df["Close"].rolling(window=short_window).mean()
            df["MA_long"] = df["Close"].rolling(window=long_window).mean()

        df["Signal"] = 0
        df.loc[short_window:, "Signal"] = (
            df["MA_short"][short_window:] > df["MA_long"][short_window:]
        ).astype(int)
        df["Position"] = df["Signal"].shift(1).fillna(0)
        df["Returns"] = df["Close"].pct_change().fillna(0)
        df["Strategy"] = df["Returns"] * df["Position"]
        df["Equity"] = (1 + df["Strategy"]).cumprod() * 100000

        # Merge benchmark
        merged = pd.merge(df, spy_df, on="Date", how="left")

        df["Trade"] = df["Signal"].diff()
        markers = df[df["Trade"] != 0][["Date", "Trade", "Equity"]].dropna()
        markers["type"] = markers["Trade"].apply(lambda x: "Buy" if x == 1 else "Sell")
        marker_points = markers[["Date", "Equity", "type"]].rename(columns={"Date": "date", "Equity": "equity"})

        # Trade log
        trade_log = []
        for i in range(1, len(df)):
            if df["Trade"].iloc[i] == 1:
                trade_log.append({"date": str(df["Date"].iloc[i]), "action": "BUY", "price": float(df["Close"].iloc[i])})
            elif df["Trade"].iloc[i] == -1:
                trade_log.append({"date": str(df["Date"].iloc[i]), "action": "SELL", "price": float(df["Close"].iloc[i])})
        trade_log = pd.DataFrame(trade_log)

        # Metrics
        final_equity = df["Equity"].iloc[-1]
        final_benchmark = merged["benchmark_equity"].iloc[-1]
        alpha = round((final_equity - final_benchmark) / final_benchmark * 100, 4)

        metrics = {
            "total_return": round((final_equity - 100000) / 100000 * 100, 4),
            "annual_return": round((df["Returns"].mean() * 252) * 100, 4),
            "sharpe_ratio": round((df["Returns"].mean() / df["Returns"].std()) * (252 ** 0.5), 4),
            "max_drawdown": round(((df["Equity"].cummax() - df["Equity"]).max()) / df["Equity"].cummax().max() * 100, 4),
            "alpha_vs_spy": alpha
        }

        equity_curve = df[["Date", "Equity"]].rename(columns={"Date": "date", "Equity": "equity"})
        benchmark_curve = merged[["Date", "benchmark_equity"]].rename(columns={"Date": "date", "benchmark_equity": "equity"})

        equity_curve["date"] = equity_curve["date"].astype(str)
        marker_points["date"] = marker_points["date"].astype(str)
        benchmark_curve["date"] = benchmark_curve["date"].astype(str)

        return {
            "metrics": {k: float(v) for k, v in metrics.items()},
            "equity_curve": equity_curve.to_dict(orient="records"),
            "benchmark_equity_curve": benchmark_curve.to_dict(orient="records"),
            "markers": marker_points.to_dict(orient="records"),
            "trades": trade_log.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception occurred in /backtest route: {str(e)}")

# ------------- END FILE -------------
