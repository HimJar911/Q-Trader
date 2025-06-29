from fastapi import APIRouter, Query
from typing import List
import yfinance as yf
import pandas as pd
import numpy as np
import traceback

router = APIRouter()

def run_strategy(df, strategy, short_window, long_window):
    print(f"🟠 run_strategy() called with: {strategy}, short={short_window}, long={long_window}")

    if "Close" not in df.columns:
        print("❌ 'Close' column missing in DataFrame!")
        print("🧾 Columns are:", df.columns)
        return None, None

    try:
        # === Moving Average Strategies ===
        if strategy == "sma":
            df["MA_short"] = df["Close"].rolling(window=short_window).mean()
            df["MA_long"] = df["Close"].rolling(window=long_window).mean()

        elif strategy == "ema":
            df["MA_short"] = df["Close"].ewm(span=short_window, adjust=False).mean()
            df["MA_long"] = df["Close"].ewm(span=long_window, adjust=False).mean()

        # === RSI + SMA Hybrid Strategy ===
        elif strategy == "rsi_sma":
            print("🔧 RSI+SMA strategy init...")

            # === Compute RSI ===
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))
            print("✅ RSI computed")

            # === Compute Moving Averages ===
            df["MA_short"] = df["Close"].rolling(window=short_window).mean()
            df["MA_long"] = df["Close"].rolling(window=long_window).mean()
            print("✅ MA_short and MA_long computed")

            df = df.dropna(subset=["RSI", "MA_short"]).copy()
            if df.empty:
                print("⚠️ DataFrame empty after dropna in rsi_sma. Skipping.")
                return None, None

            # === Define Entry & Exit Rules ===
            buy_signal = (df["RSI"] < 40) & (df["Close"] > df["MA_short"])
            sell_signal = (df["RSI"] > 70) & (df["Close"] < df["MA_short"])

            # === Encode Signals ===
            df["Signal"] = np.nan
            df.loc[buy_signal, "Signal"] = 1
            df.loc[sell_signal, "Signal"] = 0

            # === Create Position Column ===
            df["Signal"] = df["Signal"].ffill().fillna(0)  # Hold or flat
            df["Position"] = df["Signal"].shift(1).fillna(0)

            print("✅ RSI+SMA buy/sell strategy applied.")


        # === Signal/Position Logic for MA-Based Strategies ===
        if strategy in ["sma", "ema"]:
            df = df.dropna(subset=["MA_short", "MA_long"]).copy()
            df["Signal"] = (df["MA_short"] > df["MA_long"]).astype(int)
            df["Position"] = df["Signal"].shift(1).fillna(0)
            print("✅ MA-based Signal and Position set")

        if "Position" not in df.columns:
            print(f"❌ Strategy '{strategy}' did not define 'Position'")
            return None, None

        # === Backtest Calculations ===
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

        print(f"✅ Metrics computed: {metrics}")
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
        print("📊 Raw data downloaded:", df_raw.head())

        df_raw = df_raw.reset_index()

        # 🔍 Print before flattening
        print("🔍 Raw df columns before flattening:", df_raw.columns)

        # 🛠 Flatten MultiIndex columns
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = [col[0] for col in df_raw.columns]
        else:
            df_raw.columns = df_raw.columns.tolist()

        # 🔍 Print after flattening
        print("📊 Flattened final DataFrame columns:", df_raw.columns)

        result = {}
        metrics_all = {}

        for strat in strategies:
            print(f"🚀 Running strategy: {strat} ({type(strat)})")
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
            print("🛑 No valid metrics to return")
            return {"error": "No valid strategies were processed."}

        best_strategy = max(metrics_all.items(), key=lambda x: x[1]["total_return"])[0]

        return {"equities": result, "metrics": metrics_all, "best": best_strategy}

    except Exception as e:
        print("🚨 Top-level Exception in compare_strategies:", e)
        traceback.print_exc()
        return {"error": f"Server error: {str(e)}"}
