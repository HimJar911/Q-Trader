from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import traceback

router = APIRouter()

class RunGeneratedPayload(BaseModel):
    symbol: str
    start: str
    end: str
    code: str  # Python function code that returns a signal column

@router.post("/run-generated-strategy")
def run_generated_strategy(payload: RunGeneratedPayload):
    print(f"⚙️ Running user-generated strategy on: {payload.symbol}")
    
    try:
        # === STEP 1: Load stock data ===
        df = yf.download(payload.symbol, start=payload.start, end=payload.end)
        print("📦 Downloaded data:")
        print(df.head())
        print("🧾 Columns:", df.columns)

        if "Close" not in df.columns:
            return {"error": "'Close' column missing in data."}

        df = df.reset_index()

        # 🔥 Flatten MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # === STEP 2: Prepare local context for exec ===
        local_vars = {"df": df}
        print("📜 Executing user code:")
        print(payload.code)

        # === STEP 3: Execute user's strategy code ===
        try:
            exec(payload.code, local_vars, local_vars)
            print("✅ Code executed successfully.")
            print("🔍 Variables in scope after exec:", list(local_vars.keys()))
        except Exception as e:
            print("🔥 Exception during exec():", e)
            traceback.print_exc()
            return {"error": f"Code execution error: {e}"}

        # ✅ Fallback wrapper if user forgets to define `strategy(df)`
        if "strategy" not in local_vars:
            possible_funcs = [f for f in local_vars if callable(local_vars[f]) and f != "strategy"]
            if possible_funcs:
                fallback_func = possible_funcs[0]
                print(f"🛠️ Wrapping fallback: strategy(df) → {fallback_func}(df)")
                exec(f"def strategy(df): return {fallback_func}(df)", local_vars, local_vars)
            else:
                return {"error": "No valid strategy(df) or fallback function found."}

        if not callable(local_vars["strategy"]):
            return {"error": "Submitted 'strategy' is not callable."}

        # === STEP 4: Run strategy(df) to get signals ===
        try:
            signal_series = local_vars["strategy"](df)
            print("📈 Signal series generated:")
            print(signal_series.head())
        except Exception as e:
            print("🔥 Exception in strategy(df):", e)
            traceback.print_exc()
            return {"error": f"Signal generation error: {e}"}

        if signal_series is None or not isinstance(signal_series, pd.Series):
            return {"error": "Returned signal must be a pandas Series."}

        if len(signal_series) != len(df):
            return {"error": "Signal series length does not match data length."}

        df["Position"] = signal_series.shift(1).fillna(0)

        # === STEP 5: Backtest logic ===
        df["Returns"] = df["Close"].pct_change().fillna(0)
        df["Strategy"] = df["Returns"] * df["Position"]
        df["Equity"] = (1 + df["Strategy"]).cumprod() * 100000

        sharpe = 0
        if df["Strategy"].std() != 0:
            sharpe = round((df["Strategy"].mean() / df["Strategy"].std()) * (252 ** 0.5), 2)

        metrics = {
            "total_return": round((df["Equity"].iloc[-1] - 100000) / 100000 * 100, 2),
            "sharpe_ratio": sharpe,
            "max_drawdown": round(((df["Equity"].cummax() - df["Equity"]).max()) / df["Equity"].cummax().max() * 100, 2)
        }

        equity_curve = df[["Date", "Equity"]].rename(columns={"Date": "date", "Equity": "equity"})
        equity_curve["date"] = equity_curve["date"].astype(str)

        print("📊 Final Metrics:", metrics)

        return {
            "equity": equity_curve.to_dict(orient="records"),
            "metrics": metrics
        }

    except Exception as e:
        print("🔥 Top-level Exception in run_generated_strategy:", e)
        traceback.print_exc()
        return {"error": f"Server error: {e}"}
