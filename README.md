# 🚀 Advanced Event-Driven Backtesting Engine v2.0

A professional-grade, event-driven backtesting system for algorithmic trading. Now with **Dynamic Stock Data**, **Live Strategy Editor**, and a **Modern Web Dashboard**.

## 📊 New Features

### 1. 🌍 Dynamic Stock Data (yfinance)
The engine is no longer static. Use the dashboard to backtest **any ticker in the world** (e.g., `AAPL`, `TSLA`, `RELIANCE.NS`, `BTC-USD`). The system automatically downloads, formats, and caches historical data in real-time.

### 2. ✍️ Live Strategy Editor
A dedicated workspace for strategy developers. Use the **Custom Strategy** view to write high-frequency logic directly in the browser with a comprehensive variable reference guide.

### 3. 🛡️ Precision Risk Controls
Fine-tune your edge with interactive sliders:
- **Leverage Multiplier**: Amplify position sizing (up to 10x).
- **Stop-Loss & Take-Profit**: Dynamic execution and risk management.
- **Commission Friction**: Realistic transaction cost modeling.

### 4. 📈 Enhanced Visual Feedback
Real-time progress bars for data fetching and simulation stages with updated KPIs (Win Rate, Profit Factor, Sharpe Ratio).

## 📸 Visual Walkthrough

````carousel
![Dashboard Overview](./assets/dashboard_overview.png)
**Dashboard Overview**: Real-time equity curves, drawdown analysis, and dynamic strategy configuration.
<!-- slide -->
![Analytics & Performance](./assets/analytics_main.png)
**Deep Analytics**: Monthly returns heatmap, return distribution histograms, and advanced risk metrics (Sharpe, Sortino, Calmar).
<!-- slide -->
![Trade History](./assets/trade_history.png)
**Comprehensive Trade Log**: Detailed execution history with P&L tracking, duration, and side-by-side performance metrics.
<!-- slide -->
![Strategy IDE](./assets/strategy_editor.png)
**Live Strategy Editor**: Integrated development environment with real-time variable references and one-click backtesting.
````

## 📂 Project Structure
- `complete_backtest_system.py`: The core event-driven engine.
- `active_strategies.py`: Library of active trading strategies.
- `backtest_api.py`: FastAPI bridge serving engine results to the web.
- `dashboard/`: Premium Vite + React dashboard for visual analysis.
- `data/`: Automated historical CSV data storage.

## 🛠️ Installation & Setup

1. **Environment Initialization**:
   ```bash
   source .venv/bin/activate
   # OR use: .venv/bin/python3
   ```

2. **Backend API**:
   ```bash
   python3 backtest_api.py
   ```

3. **Frontend Dashboard**:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

---
*Built for quantitative traders who value realism and automation.*
