# main.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fastapi import FastAPI
from app.routes import metrics, backtest, generate
from app.performance_metrics import calculate_metrics
from app.data_loader import fetch_price_data
from app.strategy_core import sma_crossover_strategy
from app.backtester import backtest_strategy

app = FastAPI()
app.include_router(metrics.router)
app.include_router(backtest.router)
app.include_router(generate.router)

st.set_page_config(page_title="QTrader++", layout="wide")
st.title("📈 QTrader++ — Strategy Playground")

# Input UI
ticker = st.text_input("Enter Ticker Symbol", value="AAPL")
start_date = st.date_input("Start Date", value=pd.to_datetime("2019-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2024-01-01"))

if st.button("Fetch Data"):
    # Step 1: Fetch & Process Data
    df = fetch_price_data(ticker, str(start_date), str(end_date))
    df = sma_crossover_strategy(df)
    df = backtest_strategy(df)

    # Step 2: Show Strategy Signal Table
    st.subheader("Strategy Output (Tail)")
    st.dataframe(df[["Close", "SMA_Short", "SMA_Long", "Signal", "Position"]].tail(20))

    # Step 3: Chart Strategy with Buy/Sell Markers
    st.subheader("Strategy Chart")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Close"], label="Close", alpha=0.5)
    ax.plot(df["SMA_Short"], label="SMA Short (50)")
    ax.plot(df["SMA_Long"], label="SMA Long (200)")

    buy_signals = df[df["Signal"] == 1]
    sell_signals = df[df["Signal"] == -1]
    ax.scatter(buy_signals.index, buy_signals["Close"], marker="^", color="green", label="Buy", s=50)
    ax.scatter(sell_signals.index, sell_signals["Close"], marker="v", color="red", label="Sell", s=50)

    ax.set_title(f"{ticker} - SMA Crossover Strategy")
    ax.legend()
    st.pyplot(fig)

    # Step 4: Plot Portfolio Value Over Time
    st.subheader("Portfolio Value Over Time")
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(df["Portfolio Value"], label="Strategy Value", color="purple")
    ax2.set_ylabel("Portfolio ($)")
    ax2.set_title(f"{ticker} Strategy Simulation")
    ax2.legend()
    st.pyplot(fig2)

    # Step 5: Show Performance Metrics
    st.subheader("📊 Performance Metrics")

    metrics = calculate_metrics(df)
    for key, value in metrics.items():
        st.metric(label=key, value=value)

