# ----------- streamlit_app.py -----------

import streamlit as st
import requests
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import re
import textwrap


API_URL = "https://q-trader.onrender.com"

st.set_page_config(layout="wide")
st.title("💼 Q-Trader++: Quant Strategy Backtester")
strategy_options = {
    "sma": "SMA Crossover",
    "ema": "EMA Crossover",
    "rsi_sma": "RSI + SMA Hybrid",
    "macd": "MACD Signal",
    "bollinger": "Bollinger Bands",
    "roc": "Momentum (ROC)",
    "dual_sma": "Dual SMA",
    "rsi_threshold": "RSI Threshold",
}

# Sidebar navigation
st.sidebar.title("🧭 Navigation")
section = st.sidebar.radio(
    "Go to", ["Backtest Strategy", "Compare Strategies", "Generate Strategy"]
)

# -------------- COMPARE MULTIPLE STRATEGIES ------------------
if section == "Compare Strategies":
    st.header("📊 Compare Multiple Strategies")

    with st.form("compare_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Ticker Symbol", value="AAPL")
        with col2:
            start = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
        with col3:
            end = st.date_input("End Date", value=pd.to_datetime("2023-01-01"))

        # 📌 Show in Streamlit
        selected_labels = st.multiselect(
            "Select Strategies",
            options=list(strategy_options.values()),
            default=["SMA Crossover", "EMA Crossover"],
        )

        # 🔁 Map back to internal keys
        strategies = [
            key for key, label in strategy_options.items() if label in selected_labels
        ]
        short_window = st.slider("Short Window", 5, 50, 20)
        long_window = st.slider("Long Window", 20, 200, 50)

        submit_compare = st.form_submit_button("Compare Strategies")

    if submit_compare:
        with st.spinner("Comparing strategies..."):
            try:
                params = {
                    "symbol": symbol,
                    "start": start.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d"),
                    "strategies": strategies,
                    "short_window": short_window,
                    "long_window": long_window,
                }
                st.write("🛠️ Strategies being sent:", strategies)

                response = requests.get(f"{API_URL}/compare-strategies", params=params)
                data = response.json()

                if response.status_code != 200 or "error" in data:
                    st.error(f"❌ Error: {data.get('error', 'Unknown error')}")
                else:
                    st.success(f"✅ Best Performer: {data['best'].upper()}")

                    st.subheader("📈 Equity Curve Comparison")
                    fig = go.Figure()
                    for strat, records in data["equities"].items():
                        df = pd.DataFrame(records)
                        fig.add_trace(
                            go.Scatter(x=df["date"], y=df["equity"], name=strat.upper())
                        )
                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Equity",
                        hovermode="x unified",
                        template="plotly_white",
                        legend=dict(orientation="h"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("📊 Strategy Metrics")
                    metric_table = pd.DataFrame(data["metrics"]).T.reset_index()
                    metric_table.columns = [
                        "Strategy",
                        "Total Return (%)",
                        "Sharpe Ratio",
                        "Max Drawdown (%)",
                    ]
                    st.dataframe(metric_table)

            except Exception as e:
                st.error(f"Exception occurred: {e}")

# ---------- BACKTEST STRATEGY ----------
if section == "Backtest Strategy":
    st.header("📈 Backtest Moving Average Strategy")

    # Matplotlib comparison plot
    def plot_strategy_vs_benchmark_matplotlib(equity_df, benchmark_df):
        st.subheader("📉 Matplotlib Equity Comparison")

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(equity_df["date"], equity_df["equity"], label="Strategy", linewidth=2)
        ax.plot(
            benchmark_df["date"],
            benchmark_df["equity"],
            label="SPY Benchmark",
            linewidth=2,
            linestyle="--",
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Equity")
        ax.set_title("Strategy vs SPY (Matplotlib)")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

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
        selected_label = st.selectbox(
            "Strategy Type", options=list(strategy_options.values())
        )
        strategy = [k for k, v in strategy_options.items() if v == selected_label][0]

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
                try:
                    result = response.json()
                except Exception as e:
                    st.error(f"❌ Invalid response from backend: {e}")
                    st.text("Raw response:")
                    st.text(response.text)
                    st.stop()

                if response.status_code != 200:
                    st.error(f"❌ Error: {result['detail']}")
                else:
                    st.success("✅ Backtest complete!")

                    st.subheader("📊 Performance Metrics")
                    metrics_df = pd.DataFrame(
                        list(result["metrics"].items()), columns=["Metric", "Value"]
                    )
                    st.dataframe(metrics_df)

                    st.subheader("📈 Interactive Equity Curve vs SPY")
                    equity_df = pd.DataFrame(result["equity_curve"])
                    markers_df = pd.DataFrame(result["markers"])
                    benchmark_df = pd.DataFrame(
                        result.get("benchmark_equity_curve", [])
                    )

                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=equity_df["date"],
                            y=equity_df["equity"],
                            mode="lines",
                            name="Strategy Equity",
                            line=dict(color="blue"),
                        )
                    )

                    if not benchmark_df.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=benchmark_df["date"],
                                y=benchmark_df["equity"],
                                mode="lines",
                                name="SPY Benchmark",
                                line=dict(color="gray", dash="dot"),
                            )
                        )

                    if not markers_df.empty:
                        buys = markers_df[markers_df["type"] == "Buy"]
                        sells = markers_df[markers_df["type"] == "Sell"]
                        fig.add_trace(
                            go.Scatter(
                                x=buys["date"],
                                y=buys["equity"],
                                mode="markers",
                                name="Buy",
                                marker=dict(
                                    symbol="triangle-up", size=10, color="green"
                                ),
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=sells["date"],
                                y=sells["equity"],
                                mode="markers",
                                name="Sell",
                                marker=dict(
                                    symbol="triangle-down", size=10, color="red"
                                ),
                            )
                        )

                    fig.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Equity",
                        hovermode="x unified",
                        template="plotly_white",
                        legend=dict(orientation="h"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Optional Matplotlib version
                    plot_strategy_vs_benchmark_matplotlib(equity_df, benchmark_df)

                    st.subheader("🪙 Trade Log")
                    st.dataframe(pd.DataFrame(result["trades"]))

            except Exception as e:
                st.error(f"❌ Exception: {e}")

# ---------- GENERATE STRATEGY ----------
elif section == "Generate Strategy":
    st.header("🤖 Generate Trading Strategy with AI")

    with st.form("generate_form"):
        objective = st.text_area(
            "Your Objective",
            value="Generate a trading strategy using RSI and moving average for trending markets.",
        )
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
                    raw_code = result["code"]
                    clean_code = re.sub(r"```(?:python)?\s*", "", raw_code)
                    clean_code = re.sub(r"\s*```$", "", clean_code).strip()

                    st.session_state["generated_code"] = clean_code
                    st.session_state["show_generated_backtest"] = True
                    st.success("✅ Strategy generated!")

            except Exception as e:
                st.error(f"❌ Exception: {e}")

    if "generated_code" in st.session_state and st.session_state.get(
        "show_generated_backtest"
    ):
        st.subheader("🧠 Generated Strategy Code")

        edited_code = st.text_area(
            label="",
            value=st.session_state["generated_code"],
            height=400,
            label_visibility="collapsed",
            key="strategy_editor",
        )
        st.session_state["generated_code"] = edited_code

        st.subheader("⚙️ Backtest This Strategy")
        with st.form("backtest_form"):
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Ticker Symbol", value="AAPL")
            with col2:
                date_range = st.date_input(
                    "Backtest Range",
                    [pd.to_datetime("2022-01-01"), pd.to_datetime("2023-01-01")],
                )

            submit_backtest = st.form_submit_button("Run Backtest")

        if submit_backtest:
            with st.spinner("📈 Running backtest..."):
                try:
                    start_date, end_date = [str(d) for d in date_range]
                    user_code = st.session_state["generated_code"]

                    if "def strategy(" not in user_code:
                        wrapper = textwrap.dedent(
                            """
                        def strategy(df):
                            return backtest_strategy(df)
                        """
                        )
                        user_code += f"\n\n{wrapper}"

                    payload = {
                        "symbol": symbol,
                        "start": start_date,
                        "end": end_date,
                        "code": user_code,
                    }

                    response = requests.post(
                        f"{API_URL}/run-generated-strategy", json=payload
                    )
                    data = response.json()

                    if response.status_code != 200 or "error" in data:
                        st.error(
                            f"❌ Backtest Error: {data.get('error', response.status_code)}"
                        )
                        st.stop()

                    st.success("✅ Backtest completed!")
                    st.session_state["show_generated_backtest"] = False

                    # Display performance metrics
                    st.subheader("📊 Performance Metrics")
                    metrics = data["metrics"]
                    st.metric("Total Return (%)", f"{metrics['total_return']}%")
                    st.metric("Sharpe Ratio", metrics["sharpe_ratio"])
                    st.metric("Max Drawdown (%)", f"{metrics['max_drawdown']}%")

                    st.subheader("📈 Equity Curve")
                    equity_df = pd.DataFrame(data["equity"])
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=equity_df["date"],
                            y=equity_df["equity"],
                            mode="lines",
                            name="Equity",
                        )
                    )
                    fig.update_layout(
                        title="Equity Over Time",
                        xaxis_title="Date",
                        yaxis_title="Equity ($)",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ Exception during backtest: {e}")

# ----------- END FILE -----------
