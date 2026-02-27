# Q-Trader++

> **LLM-Powered Quantitative Backtesting Platform**
> Build, test, and compare trading strategies — with an AI that writes the code for you.

---

## Overview

Q-Trader++ is a full-stack quant backtesting platform that lets you test trading strategies against real historical data without touching a spreadsheet. Describe a strategy in plain English, get back runnable Python, run the backtest, and compare it against anything else you've built — all from a clean dashboard.

FastAPI backend. Streamlit frontend. No kernel restarts. No goat sacrifices.

---

## Features

- **Strategy Backtesting** — Test SMA, RSI-SMA hybrids, and custom threshold logic against real historical price data
- **LLM Strategy Generation** — Type a plain-English prompt like "momentum strategy for tech stocks" and get back working Python code
- **Side-by-Side Comparison** — Run multiple strategies simultaneously and compare them on a unified performance view
- **Rich Performance Metrics** — Equity curve, total returns, max drawdown, Sharpe ratio, and win rate all in one place
- **Modular & Extendable** — Clean separation between backend logic and frontend UI, easy to build on

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Language | Python |
| Deployment | Render |

---

## Project Structure

```
Q-Trader/
├── app/                # Core backtesting engine and strategy modules
├── main.py             # FastAPI entry point
├── streamlit_app.py    # Streamlit dashboard
├── requirements.txt    # Python dependencies
├── render.yaml         # Render deployment config
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HimJar911/Q-Trader.git
   cd Q-Trader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend**
   ```bash
   python main.py
   ```

4. **Launch the dashboard**
   ```bash
   streamlit run streamlit_app.py
   ```

---

## Usage

1. Select a **stock ticker** and **date range**
2. Choose a built-in strategy or enter a plain-English prompt to **generate one via LLM**
3. Run the backtest and review your **equity curve, Sharpe ratio, drawdown, and win rate**
4. Stack multiple strategies in the **comparison view** to see how they perform against each other

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## License

This project is open source. See [LICENSE](LICENSE) for details.
