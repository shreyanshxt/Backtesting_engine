# 🚀 Advanced Event-Driven Backtesting Engine v2.0

A professional-grade, event-driven backtesting system for algorithmic trading. Now with **Market Regime Detection**, **Multi-Strategy Coordination**, and a **Modern Web Dashboard**.

## 📂 Project Structure
- `complete_backtest_system.py`: The core event-driven engine with JSON export.
- `active_strategies.py`: Library of active trading strategies including `MultiStrategyRunner`.
- `run_advanced_backtest.py`: [NEW] Demo of regime-aware multi-strategy execution.
- `backtest_api.py`: [UPDATED] FastAPI bridge serving engine results to the web.
- `dashboard/`: [NEW] Premium Vite + React dashboard for visual analysis.
- `data/`: Historical CSV data storage.

## 🛠️ Installation & Setup
1. **Environment**:
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run Advanced Engine**:
   ```bash
   python run_advanced_backtest.py
   ```
3. **Launch Dashboard**:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

## 📊 New Features
### 1. Market Regime Detection
Automatically identifies `TRENDING`, `RANGING`, and `HIGH_VOL` markets using ADX and ATR metrics.
### 2. Multi-Strategy Gating
Runs multiple strategies (e.g., Momentum + Mean Reversion) but only triggers signals when the market regime matches the strategy's optimal conditions.
### 3. Premium Web Dashboard
Interactive equity curves, drawdown analysis, and recent execution logs with a modern dark-mode aesthetic.

---
*Built for quantitative traders who value realism and automation.*
