# app/routes/metrics.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
from app.performance_metrics import calculate_metrics

router = APIRouter()

class PortfolioData(BaseModel):
    dates: list[str]       # ISO date strings: ["2023-01-01", "2023-01-02", ...]
    values: list[float]    # Corresponding portfolio values: [10000, 10200, 10150, ...]

@router.post("/evaluate-strategy")
def evaluate_strategy(data: PortfolioData):
    if len(data.dates) != len(data.values):
        raise HTTPException(status_code=400, detail="Length mismatch: dates and values")

    try:
        series = pd.Series(data.values, index=pd.to_datetime(data.dates))
        metrics = calculate_metrics(series)
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def compare_strategy_vs_benchmark(strategy_df, benchmark_df):
    merged = pd.merge(strategy_df, benchmark_df, left_index=True, right_index=True, how="inner")
    merged["Strategy Returns"] = merged["Portfolio Value"].pct_change()
    merged["Benchmark Returns"] = merged["Benchmark"].pct_change()

    merged["Strategy Cumulative"] = (1 + merged["Strategy Returns"]).cumprod()
    merged["Benchmark Cumulative"] = (1 + merged["Benchmark Returns"]).cumprod()

    return merged
