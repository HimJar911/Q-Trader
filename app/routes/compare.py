from fastapi import APIRouter, Query
from typing import List
import yfinance as yf
import pandas as pd
import numpy as np
import traceback
from app.strategy_core import (
    sma_crossover_strategy,
    ema_crossover_strategy, rsi_sma_strategy,
    macd_strategy,
    bollinger_strategy,
    momentum_roc_strategy,
    dual_sma_strategy,
    rsi_threshold_strategy
)

router = APIRouter()

# ✅ NEW STRATEGY MAP
strategy_map = {
    "sma": sma_crossover_strategy,
    "macd": macd_strategy,
    "ema": ema_crossover_strategy,
    "rsi_sma": rsi_sma_strategy,
    "bollinger": bollinger_strategy,
    "roc": momentum_roc_strategy,
    "dual_sma": dual_sma_strategy,
    "rsi_threshold": rsi_threshold_strategy
}

def run_strategy(df, strategy, short_window, long_window):
    print(f"🟠 run_strategy() called with: {strategy}, short={short_window}, long={long_window}")

    if "Close" not in df.columns:
        print("❌ 'Close' column missing in DataFrame!")
        return None, None

    try:
        # ✅ If it's in our strategy map, run that function directly
        if strategy in strategy_map:
            df = strategy_map[strategy](df)

        if "Signal" not in df.columns:
            print(f"❌ Strategy '{strategy}' did not produce 'Signal'")
            return None, None

        # ✅ Common logic
        df["Position"] = df["Signal"].shift(1).fillna(0)
        df["Returns"] = df["Close"].pct_change().fillna(0)
        df["Strategy"] = df["Returns"] * df["Position"]
        df["Equity"] = (1 + df["Strategy"]).cumprod() * 100000

        sharpe = 0
        if df["Strategy"].std() != 0:
            sharpe = round((df["Strategy"].mean() / df["Strategy"].std()) * np.sqrt(252), 2)

        metrics = {
            "total_return": round((df["Equity"].iloc[-1] - 100000) / 100000 * 100, 2),
            "sharpe_ratio": sharpe,
            "max_drawdown": round(((df["Equity"].cummax() - df["Equity"]).max()) / df["Equity"].cummax().max() * 100, 2)
        }

        return df[["Date", "Equity"]], metrics

    except Exception as e:
        print("🔥 Exception in run_strategy:", e)
        traceback.print_exc()
        return None, None


@router.get("/compare-strategies")
def compare_strategies(
    symbol: str,
    start: str,
    end: str,
    strategies: List[str] = Query(...),
    short_window: int = 20,
    long_window: int = 50
):
    try:
        print("📥 compare_strategies called with:", symbol, start, end, strategies)
        df_raw = yf.download(symbol, start=start, end=end)
        df_raw = df_raw.reset_index()

        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = [col[0] for col in df_raw.columns]
        else:
            df_raw.columns = df_raw.columns.tolist()

        result = {}
        metrics_all = {}

        for strat in strategies:
            print(f"🚀 Running strategy: {strat}")
            df_copy = df_raw.copy()
            equity_df, metrics = run_strategy(df_copy, strat, short_window, long_window)

            if equity_df is None or metrics is None:
                print(f"❌ Skipping invalid strategy: {strat}")
                continue

            equity_df = equity_df.rename(columns={"Date": "date", "Equity": "equity"})
            colname = f"{strat}_equity"
            equity_df.rename(columns={"equity": colname}, inplace=True)

            records = [
                {"date": str(row["date"]), "equity": float(row[colname])}
                for _, row in equity_df.iterrows()
            ]

            result[strat] = records
            metrics_all[strat] = {k: float(v) for k, v in metrics.items()}

        if not metrics_all:
            return {"error": "No valid strategies were processed."}

        best_strategy = max(metrics_all.items(), key=lambda x: x[1]["total_return"])[0]

        return {"equities": result, "metrics": metrics_all, "best": best_strategy}

    except Exception as e:
        print("🚨 Top-level Exception in compare_strategies:", e)
        traceback.print_exc()
        return {"error": f"Server error: {str(e)}"}
