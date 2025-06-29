# ----------- streamlit_app.py -----------

import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

# Interactive equity curve plot
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

# ---------- CONFIG ----------
API_URL = "http://127.0.0.1:8000"
st.set_page_config(layout="wide")
st.title("💼 Q-Trader++: Quant Strategy Backtester")

# ---------- NAVIGATION ----------
st.sidebar.title("🧭 Navigation")
section = st.sidebar.radio("Go to", ["Backtest Strategy", "Generate Strategy"])

# ---------- BACKTEST STRATEGY ----------
if section == "Backtest Strategy":
    st.header("📈 Backtest Moving Average Strategy")

    with st.form("backtest_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Stock Symbol", value="AAPL")
        with col2:
            start = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
        with col3:
            end = st.date_input("End Date", value=pd.to_datetime("2023-01-01"))

        short_window = st.slider("Short MA Window", 5, 100, 20)
        long_window = st.slider("Long MA Window", 10, 200, 50)
        strategy = st.selectbox("Strategy Type", ["sma", "ema"])

        submitted = st.form_submit_button("Run Backtest")

    if submitted:
        with st.spinner("Running backtest..."):
            try:
                params = {
                    "symbol": symbol,
                    "start": start.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d"),
                    "short_window": short_window,
                    "long_window": long_window,
                    "strategy": strategy,
                }
                response = requests.get(f"{API_URL}/backtest", params=params)
                result = response.json()

                if response.status_code != 200:
                    st.error(f"❌ Error: {result['detail']}")
                else:
                    st.success("✅ Backtest complete!")

                    # ---- Metrics ----
                    st.subheader("📊 Performance Metrics")
                    metrics_df = pd.DataFrame(list(result["metrics"].items()), columns=["Metric", "Value"])
                    st.dataframe(metrics_df)

                    # ---- Interactive Equity Plot ----
                    st.subheader("🏋️ Equity Curve (Interactive)")
                    equity_df = pd.DataFrame(result["equity_curve"])
                    markers_df = pd.DataFrame(result["markers"])

                    equity_data = equity_df.to_dict(orient="records")
                    markers_data = markers_df.to_dict(orient="records")

                    fig = plot_equity_curve_interactive(equity_data, markers_data)
                    st.plotly_chart(fig, use_container_width=True)

                    # ---- Trade Log ----
                    st.subheader("🪙 Trade Log")
                    trades_df = pd.DataFrame(result["trades"])
                    st.dataframe(trades_df)

            except Exception as e:
                st.error(f"❌ Exception: {e}")

# ---------- GENERATE STRATEGY ----------
elif section == "Generate Strategy":
    st.header("🤖 Generate Trading Strategy with AI")

    with st.form("generate_form"):
        objective = st.text_area("Your Objective", value="Generate a trading strategy using RSI and moving average for trending markets.")
        submit_gen = st.form_submit_button("Generate Strategy")

    if submit_gen:
        with st.spinner("Contacting LLM agent..."):
            try:
                payload = {"objective": objective}
                response = requests.post(f"{API_URL}/generate-strategy", json=payload)
                result = response.json()

                if response.status_code != 200:
                    st.error(f"❌ Error: {result['detail']}")
                else:
                    st.success("✅ Strategy generated!")
                    st.subheader("📜 Strategy Code")
                    st.code(result['code'], language="python")

            except Exception as e:
                st.error(f"❌ Exception: {e}")

# ----------- END FILE -----------
