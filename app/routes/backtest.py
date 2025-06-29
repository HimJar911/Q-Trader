# ----------- app/routes/backtest.py -----------

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import traceback

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
        print("📦 [1] Downloading data...")
        df = yf.download(symbol, start=start, end=end)
        df.columns = df.columns.get_level_values(0)  # 🧼 flatten MultiIndex columns
        df = df.reset_index()
        print("✅ [2] Data head:\n", df.head())

        # Strategy logic
        if strategy.lower() == "ema":
            print("⚙️ [3] Running EMA Strategy...")
            df["MA_short"] = df["Close"].ewm(span=short_window, adjust=False).mean()
            df["MA_long"] = df["Close"].ewm(span=long_window, adjust=False).mean()
        else:
            print("⚙️ [3] Running SMA Strategy...")
            df["MA_short"] = df["Close"].rolling(window=short_window).mean()
            df["MA_long"] = df["Close"].rolling(window=long_window).mean()

        df["Signal"] = 0
        df.loc[short_window:, "Signal"] = (
            df["MA_short"][short_window:] > df["MA_long"][short_window:]
        ).astype(int)
        df["Position"] = df["Signal"].shift(1).fillna(0)
        df["Returns"] = df["Close"].pct_change().fillna(0)
        df["Strategy"] = df["Returns"] * df["Position"]

        initial_cash = 100000
        df["Equity"] = (1 + df["Strategy"]).cumprod() * initial_cash

        df["Trade"] = df["Signal"].diff()
        markers = df[df["Trade"] != 0][["Date", "Trade", "Equity"]].dropna()
        markers["type"] = markers["Trade"].apply(lambda x: "Buy" if x == 1 else "Sell")

        marker_points = markers[["Date", "Equity", "type"]].rename(columns={"Date": "date", "Equity": "equity"})

        # 📜 Build trade log
        trade_log = []
        for i in range(1, len(df)):
            if df["Trade"].iloc[i] == 1:
                price = float(df["Close"].iloc[i])
                trade_log.append({
                    "date": str(df["Date"].iloc[i]),
                    "action": "BUY",
                    "price": price
                })
            elif df["Trade"].iloc[i] == -1:
                price = float(df["Close"].iloc[i])
                trade_log.append({
                    "date": str(df["Date"].iloc[i]),
                    "action": "SELL",
                    "price": price
                })
        trade_log = pd.DataFrame(trade_log)

        # 📊 Metrics
        metrics = {
            "total_return": round((df["Equity"].iloc[-1] - initial_cash) / initial_cash * 100, 4),
            "annual_return": round((df["Returns"].mean() * 252) * 100, 4),
            "sharpe_ratio": round((df["Returns"].mean() / df["Returns"].std()) * (252 ** 0.5), 4),
            "max_drawdown": round(((df["Equity"].cummax() - df["Equity"]).max()) / df["Equity"].cummax().max() * 100, 4)
        }

        # 🔍 Debug logs
        print("📈 [4] Metrics:\n", metrics)
        print("📉 [5] Equity Curve Sample:\n", df[['Date', 'Equity']].head(2).to_dict(orient="records"))
        print("📍 [6] Marker Points:\n", marker_points.head(2).to_dict(orient="records"))
        print("🧾 [7] Trade Log Sample:\n", trade_log.head(2).to_dict(orient="records"))

        # ✅ Format for response
        equity_curve = df[["Date", "Equity"]].rename(columns={"Date": "date", "Equity": "equity"})
        equity_curve["date"] = equity_curve["date"].astype(str)
        marker_points["date"] = marker_points["date"].astype(str)

        print("✅ [8] Returning Response JSON")
        return {
            "metrics": {k: float(v) for k, v in metrics.items()},
            "equity_curve": equity_curve.to_dict(orient="records"),
            "markers": marker_points.to_dict(orient="records"),
            "trades": trade_log.to_dict(orient="records")
        }

    except Exception as e:
        print("❌ [FATAL ERROR] in /backtest route:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Exception occurred in /backtest route: {str(e)}")
    
def plot_equity_curve_interactive(equity_curve, markers):
    fig = go.Figure()

    # Equity line
    fig.add_trace(go.Scatter(
        x=[point["date"] for point in equity_curve],
        y=[point["equity"] for point in equity_curve],
        mode="lines",
        name="Equity",
        line=dict(color="blue")
    ))

    # Buy markers
    buys = [m for m in markers if m["type"] == "Buy"]
    fig.add_trace(go.Scatter(
        x=[b["date"] for b in buys],
        y=[b["equity"] for b in buys],
        mode="markers",
        marker=dict(symbol="triangle-up", color="green", size=10),
        name="Buy"
    ))

    # Sell markers
    sells = [m for m in markers if m["type"] == "Sell"]
    fig.add_trace(go.Scatter(
        x=[s["date"] for s in sells],
        y=[s["equity"] for s in sells],
        mode="markers",
        marker=dict(symbol="triangle-down", color="red", size=10),
        name="Sell"
    ))

    fig.update_layout(
        title="📈 Equity Over Time",
        xaxis_title="Date",
        yaxis_title="Equity",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig

# ----------- END FILE -----------
