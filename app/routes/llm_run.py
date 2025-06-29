from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import traceback
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
router = APIRouter()

class StrategyRunRequest(BaseModel):
    symbol: str
    start: str
    end: str
    code: str  # Python code defining a function `custom_strategy(df)`

@router.post("/run-generated-strategy")
def run_generated_strategy(payload: StrategyRunRequest):
    try:
        # 1. Download historical stock data
        df = yf.download(payload.symbol, start=payload.start, end=payload.end)
        if df.empty:
            raise ValueError("Stock data could not be downloaded.")
        df = df.reset_index()

        # 2. Inject generated strategy code
        local_scope = {}
        try:
            exec(payload.code, {}, local_scope)
        except Exception as e:
            raise ValueError(f"❌ Error while executing code: {e}")

        if "custom_strategy" not in local_scope:
            raise ValueError("The code must define a function named 'custom_strategy(df)'")

        # 3. Call the custom strategy function
        try:
            df = local_scope["custom_strategy"](df)
        except Exception as e:
            raise ValueError(f"❌ Error while running custom_strategy(): {e}")

        if "Position" not in df.columns:
            raise ValueError("Your strategy must return a DataFrame with a 'Position' column.")

        # 4. Calculate returns & equity curve
        df["Returns"] = df["Close"].pct_change().fillna(0)
        df["Strategy"] = df["Returns"] * df["Position"]
        df["Equity"] = (1 + df["Strategy"]).cumprod() * 100000

        sharpe = 0
        if df["Strategy"].std() != 0:
            sharpe = round((df["Strategy"].mean() / df["Strategy"].std()) * np.sqrt(252), 2)

        max_drawdown = round(((df["Equity"].cummax() - df["Equity"]).max()) / df["Equity"].cummax().max() * 100, 2)
        total_return = round((df["Equity"].iloc[-1] - 100000) / 100000 * 100, 2)

        metrics = {
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "total_return": total_return,
        }

        records = [
            {"date": str(row["Date"]), "equity": float(row["Equity"])}
            for _, row in df.iterrows()
        ]

        return {
            "equity": records,
            "metrics": metrics
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
