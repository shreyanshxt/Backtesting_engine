import numpy as np
import pandas as pd
from scipy.optimize import newton,brentq


class PerformanceStats:
    def __init__(self, equity_df: pd.DataFrame, cash_flows: list):
        self.equity = equity_df.copy()
        self.cash_flows = cash_flows

    # ---------- CORE METRICS ----------

    def cagr(self):
        start = self.equity.index[0]
        end = self.equity.index[-1]
        years = (end - start).days / 365.25

        start_val = self.equity["total"].iloc[0]
        end_val = self.equity["total"].iloc[-1]

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

    def calmar_ratio(self):
        _, max_dd, _ = self.drawdowns()
        return self.cagr() / abs(max_dd) if max_dd != 0 else np.nan

    # ---------- SUMMARY ----------

    def summary(self):
        drawdown, max_dd, dd_duration = self.drawdowns()

        self.equity["drawdown"] = drawdown

        return {
            "Final Equity": round(self.equity["total"].iloc[-1], 2),
            "CAGR (%)": round(self.cagr() * 100, 2),
         
            "Volatility (%)": round(self.volatility() * 100, 2),
            "Max Drawdown (%)": round(max_dd * 100, 2),
            "Drawdown Duration (days)": int(dd_duration),
            "Calmar Ratio": round(self.calmar_ratio(), 2),
        }

import matplotlib.pyplot as plt 

class PerformanceVisuals:
    def __init__(self,equity_df):
        self.equity =equity_df

    def plot_equity_curve(self):
        plt.figure(figsize=(12,5))
        plt.plot(self.equity.index,self.equity["total"])
        plt.title("Equity Curve")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Values")
        plt.grid(True)
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
        self.plot_equity_curve()
        self.plot_drawdown()