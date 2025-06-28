# streamlit_app.py

import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")
st.title("💼 Q-Trader++: Quant Strategy Backtester")

# Sidebar navigation
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

        short_window = st.slider("Short Moving Average Window", 5, 100, 20)
        long_window = st.slider("Long Moving Average Window", 10, 200, 50)
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
                }
                response = requests.get(f"{API_URL}/backtest", params=params)
                result = response.json()

                if response.status_code != 200:
                    st.error(f"❌ Error: {result['detail']}")
                else:
                    st.success("✅ Backtest complete!")
                    st.subheader("📊 Performance Metrics")
                    st.write(result["metrics"])

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
