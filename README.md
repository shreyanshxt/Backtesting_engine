# 🚀 Advanced Event-Driven Backtesting Engine v2.0

A professional-grade, event-driven backtesting system for algorithmic trading. Now with **Market Regime Detection**, **Multi-Strategy Coordination**, and a **Modern Web Dashboard**.

## 📂 Project Structure
- `complete_backtest_system.py`: The core event-driven engine.
- `active_strategies.py`: Library of active trading strategies including `MultiStrategyRunner`.
- `run_advanced_backtest.py`: Demo of regime-aware multi-strategy execution.
- `run_active_backtest.py`: Comprehensive test runner evaluating all active strategies.
- `riskstats.py`: Advanced mathematical library for performance metrics (CAGR, Calmar, Sortino).
- `backtest_api.py`: FastAPI bridge serving engine results to the web.
- `dashboard/`: Premium Vite + React dashboard for visual analysis (Dynamic KPI Grid & Custom Code Editor).
- `data/`: Historical CSV data storage.

## 🛠️ Installation & Setup
1. **Environment**:
   The engine MUST be run using its dedicated virtual environment:
   ```bash
   source .venv/bin/activate
   # OR use the executable directly: .venv/bin/python3
   ```
2. **Run the Individual Strategy Evaluation Suite**:
   ```bash
   .venv/bin/python3 run_active_backtest.py
   ```
3. **Run the Advanced Regime-Gated Multi-Strategy**:
   ```bash
   .venv/bin/python3 run_advanced_backtest.py
   ```
3. **Launch Dashboard**:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

## 📸 Dashboard Demonstration
![Dashboard Interaction Demo](./assets/dashboard_demo.webp)

## 📊 New Features
### 1. Market Regime Detection
Automatically identifies `TRENDING`, `RANGING`, and `HIGH_VOL` markets using ADX and ATR metrics.
### 2. Multi-Strategy Gating
Runs multiple strategies (e.g., Momentum + Mean Reversion) but only triggers signals when the market regime matches the strategy's optimal conditions.
### 3. Premium Web Dashboard
Interactive equity curves, drawdown analysis, and recent execution logs with a modern dark-mode aesthetic.

---
*Built for quantitative traders who value realism and automation.*
