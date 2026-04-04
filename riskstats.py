import numpy as np
import pandas as pd
from scipy.optimize import newton,brentq


class PerformanceStats:
    def __init__(self, equity_df: pd.DataFrame, cash_flows: list, closed_trades: list = None):
        self.equity = equity_df.copy()
        self.cash_flows = cash_flows
        self.closed_trades = closed_trades if closed_trades else []

    # ---------- CORE METRICS ----------

    def cagr(self):
        start = self.equity.index[0]
        end = self.equity.index[-1]
        days = (end - start).days
        if days <= 0: return 0
        years = days / 365.25

        start_val = self.equity["total"].iloc[0]
        end_val = self.equity["total"].iloc[-1]
        
        if start_val <= 0: return 0
        return (end_val / start_val) ** (1 / years) - 1

    def volatility(self):
        return self.equity["returns"].std() * np.sqrt(252)

    # ---------- DRAWdowns ----------

    def drawdowns(self):
        cumulative = self.equity["total"]
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak

        max_dd = drawdown.min()
        duration = (drawdown != 0).astype(int).groupby(
            (drawdown == 0).astype(int).cumsum()
        ).sum().max()

        return drawdown, max_dd, duration

    # ---------- RATIOS ----------

    def sharpe_ratio(self, risk_free_rate=0.0):
        mean_return = self.equity["returns"].mean() * 252
        vol = self.volatility()
        return (mean_return - risk_free_rate) / vol if vol != 0 else 0

    def sortino_ratio(self, risk_free_rate=0.0):
        mean_return = self.equity["returns"].mean() * 252
        downside_returns = self.equity[self.equity["returns"] < 0]["returns"]
        downside_vol = downside_returns.std() * np.sqrt(252)
        return (mean_return - risk_free_rate) / downside_vol if downside_vol != 0 else 0

    def calmar_ratio(self):
        _, max_dd, _ = self.drawdowns()
        return self.cagr() / abs(max_dd) if max_dd != 0 else np.nan

    # ---------- PROFITABILITY & TRADE STATS ----------

    def trade_metrics(self):
        if not self.closed_trades:
            return {}
        
        pnls = [t['pnl'] for t in self.closed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        win_rate = len(wins) / len(pnls) if pnls else 0
        
        # Profit Factor: Gross Profit / Gross Loss
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
        
        # Expectancy: (Win Rate * Avg Win) + (Loss Rate * Avg Loss)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Avg Duration (hours)
        durations = [t['duration'] for t in self.closed_trades]
        avg_duration = np.mean(durations) if durations else 0
        
        # Win/Loss Streaks
        current_streak = 0
        win_streaks = []
        loss_streaks = []
        is_winning = None
        
        for p in pnls:
            winning = p > 0
            if is_winning is None:
                is_winning = winning
                current_streak = 1
            elif is_winning == winning:
                current_streak += 1
            else:
                if is_winning: win_streaks.append(current_streak)
                else: loss_streaks.append(current_streak)
                is_winning = winning
                current_streak = 1
        
        # Append last streak
        if is_winning is True: win_streaks.append(current_streak)
        elif is_winning is False: loss_streaks.append(current_streak)
        
        return {
            "Total Trades": len(pnls),
            "Win Rate (%)": round(win_rate * 100, 2),
            "Profit Factor": round(profit_factor, 2),
            "Expectancy": round(expectancy, 2),
            "Avg Win": round(avg_win, 2),
            "Avg Loss": round(avg_loss, 2),
            "Avg Trade Duration (hrs)": round(avg_duration, 2),
            "Max Win Streak": max(win_streaks) if win_streaks else 0,
            "Max Loss Streak": max(loss_streaks) if loss_streaks else 0
        }

    # ---------- BENCHMARK & ALPHA/BETA ----------

    def alpha_beta(self):
        """
        Calculates Beta and Alpha (annualized) relative to the benchmark.
        Requires 'benchmark' column to be present in equity_df.
        """
        if 'benchmark' not in self.equity.columns:
            return 0.0, 0.0
            
        # Calculate returns
        returns = self.equity['total'].pct_change().dropna()
        bench_returns = self.equity['benchmark'].pct_change().dropna()
        
        # Align indices
        common_index = returns.index.intersection(bench_returns.index)
        returns = returns.loc[common_index]
        bench_returns = bench_returns.loc[common_index]
        
        if len(returns) < 2:
            return 0.0, 0.0

        # Linear regression: R_p = alpha + beta * R_b
        # Using numpy polyfit for simplicity
        beta, alpha_daily = np.polyfit(bench_returns, returns, 1)
        
        # Annualize Alpha
        # Alpha_annual = (1 + alpha_daily)^252 - 1 (or simplified as alpha_daily * 252)
        alpha_annual = alpha_daily * 252
        
        return round(alpha_annual, 4), round(beta, 4)

    # ---------- SUMMARY ----------

    def summary(self):
        drawdown, max_dd, dd_duration = self.drawdowns()
        self.equity["drawdown"] = drawdown

        res = {
            "Final Equity": round(self.equity["total"].iloc[-1], 2),
            "CAGR (%)": round(self.cagr() * 100, 2),
            "Sharpe Ratio": round(self.sharpe_ratio(), 2),
            "Sortino Ratio": round(self.sortino_ratio(), 2),
            "Max Drawdown (%)": round(max_dd * 100, 2),
            "Calmar Ratio": round(self.calmar_ratio(), 2),
        }

        # Alpha/Beta
        if 'benchmark' in self.equity.columns:
            alpha, beta = self.alpha_beta()
            res["Alpha (Annual)"] = alpha
            res["Beta"] = beta
            
            # Benchmark CAGR
            bench_start = self.equity["benchmark"].iloc[0]
            bench_end = self.equity["benchmark"].iloc[-1]
            days = (self.equity.index[-1] - self.equity.index[0]).days
            if days > 0:
                years = days / 365.25
                bench_cagr = (bench_end / bench_start) ** (1 / years) - 1
                res["Benchmark CAGR (%)"] = round(bench_cagr * 100, 2)

        # Add Trade metrics
        trades = self.trade_metrics()
        res.update(trades)

        # Sanitize for JSON compliance (No NaN/Inf)
        for k, v in res.items():
            if isinstance(v, (float, np.float64, np.float32)):
                if np.isnan(v) or np.isinf(v):
                    res[k] = 0.0
        
        return res

try:
    import matplotlib.pyplot as plt 
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

class PerformanceVisuals:
    def __init__(self, equity_df):
        self.equity = equity_df

    def plot_equity_curve(self):
        plt.figure(figsize=(12,6))
        plt.plot(self.equity.index, self.equity["total"], label="Portfolio", color='blue')
        
        if 'benchmark' in self.equity.columns:
            plt.plot(self.equity.index, self.equity["benchmark"], label="Benchmark", color='gray', linestyle='--')
            
        plt.title("Equity Curve vs Benchmark")
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    def plot_drawdown(self):
        plt.figure(figsize=(12,4))
        plt.fill_between(
            self.equity.index,
            self.equity["drawdown"],
            0,
        )
        plt.title("Drawdown Curve")
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)
        plt.show()
        
    
    def plot_all(self):
        if HAS_MATPLOTLIB:
            self.plot_equity_curve()
            self.plot_drawdown()
        else:
            print("\n[WARNING] Matplotlib not found. Skipping plots.")