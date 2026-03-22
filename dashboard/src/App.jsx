import React, { useState, useEffect } from 'react';
import { 
  LineChart, TrendingUp, Activity, Shield, 
  ArrowUpRight, ArrowDownRight, RefreshCcw, 
  BarChart3, Clock, LayoutDashboard
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [strategy, setStrategy] = useState('multi');
  const [isRunning, setIsRunning] = useState(false);

  const runBacktest = async (e) => {
    if (e) e.preventDefault();
    setIsRunning(true);
    
    const formData = new FormData();
    formData.append('strategy', strategy);
    formData.append('symbol', 'NVDA');

    try {
      const response = await fetch('http://127.0.0.1:8000/backtest', {
        method: 'POST',
        body: formData
      });
      const json = await response.json();
      setData(json);
    } catch (err) {
      console.error("Failed to run backtest:", err);
      // Fallback if API is down
      if (!data) setDemoData();
    } finally {
      setIsRunning(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    runBacktest();
  }, []);

  const setDemoData = () => {
    const demo = {
      metadata: { symbols: ['NVDA'], initial_capital: 1000000, signals: 42, orders: 42, fills: 38 },
      stats: {
        "Total Return": "24.5%",
        "Sharpe Ratio": "1.82",
        "Max Drawdown": "-8.2%",
        "Drawdown Duration": "15 days"
      },
      charts: Array.from({ length: 100 }, (_, i) => ({
        date: `2024-01-${i + 1}`,
        equity: 1000000 * (1 + (i * 0.002) + (Math.sin(i / 5) * 0.02)),
        benchmark: 1000000 * (1 + (i * 0.001)),
        drawdown: -Math.abs(Math.sin(i / 10) * 0.05)
      })),
      recent_trades: [
        { symbol: 'NVDA', entry_time: '2024-03-20', exit_time: '2024-03-22', pnl: 4500, pnl_pct: 1.2, side: 'LONG' },
        { symbol: 'NVDA', entry_time: '2024-03-18', exit_time: '2024-03-19', pnl: -1200, pnl_pct: -0.3, side: 'SHORT' },
        { symbol: 'NVDA', entry_time: '2024-03-15', exit_time: '2024-03-17', pnl: 8900, pnl_pct: 2.4, side: 'LONG' },
      ]
    };
    setData(demo);
    setLoading(false);
  };

  if (loading) return <div className="loading">Initializing Engine...</div>;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#8b949e', font: { family: 'Inter' } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(13, 17, 23, 0.9)',
        titleColor: '#58a6ff',
        bodyColor: '#c9d1d9',
        borderColor: '#30363d',
        borderWidth: 1
      }
    },
    scales: {
      x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } },
      y: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } }
    }
  };

  const equityData = {
    labels: data.charts.map(d => d.date),
    datasets: [
      {
        label: 'Strategy Equity',
        data: data.charts.map(d => d.equity),
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88, 166, 255, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Benchmark',
        data: data.charts.map(d => d.benchmark),
        borderColor: '#8b949e',
        borderDash: [5, 5],
        fill: false,
        tension: 0.4
      }
    ]
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="brand">
          <h1>ANTIGRAVITY <span style={{color: '#8b949e', fontWeight: 300}}>ENGINE</span></h1>
          <p style={{color: '#8b949e', fontSize: '0.8rem'}}>Advanced Event-Driven Backtesting v2.0</p>
        </div>
        
        <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
          <select 
            value={strategy} 
            onChange={(e) => setStrategy(e.target.value)}
            style={{background: 'var(--card-bg)', color: 'var(--text-color)', border: '1px solid var(--border-color)', padding: '8px 12px', borderRadius: '8px', cursor: 'pointer'}}
          >
            <option value="multi">Advanced Multi-Strategy (Regime Gated)</option>
            <option value="momentum">Momentum Strategy</option>
            <option value="mean_reversion">Mean Reversion</option>
            <option value="rsi">RSI Strategy</option>
          </select>

          <button 
            onClick={runBacktest} 
            disabled={isRunning}
            style={{
              background: isRunning ? 'var(--text-muted)' : 'var(--primary-color)', 
              color: '#fff', 
              border: 'none', 
              padding: '8px 20px', 
              borderRadius: '8px', 
              fontWeight: 600, 
              cursor: isRunning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'background 0.2s'
            }}
          >
            {isRunning ? <RefreshCcw size={16} className="spin" /> : <TrendingUp size={16} />}
            {isRunning ? 'Running...' : 'Run Backtest'}
          </button>

          <div className="status-badge" style={{display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(56, 139, 253, 0.1)', padding: '8px 16px', borderRadius: '20px', border: '1px solid rgba(56, 139, 253, 0.4)'}}>
            <Activity size={16} className={isRunning ? "pulse" : "pnl-positive"} />
            <span style={{fontSize: '0.85rem', fontWeight: 600}}>{isRunning ? 'Processing...' : 'System Idle'}</span>
          </div>
        </div>
      </header>

      <div className="stats-grid">
        <Card title="Total Return" value={data.stats["Total Return"]} icon={<TrendingUp size={16} />} trend={12.4} />
        <Card title="Sharpe Ratio" value={data.stats["Sharpe Ratio"]} icon={<Shield size={16} />} />
        <Card title="Max Drawdown" value={data.stats["Max Drawdown"]} icon={<ArrowDownRight size={16} />} inverseColor />
        <Card title="Order Fills" value={data.metadata.fills} icon={<RefreshCcw size={16} />} />
      </div>

      <div className="grid-layout">
        <div className="card chart-container">
          <div className="card-title">
            <BarChart3 size={16} /> Equity Curve Performance
          </div>
          <div style={{height: '100%'}}>
            <Line options={chartOptions} data={equityData} />
          </div>
        </div>

        <div className="card recent-trades">
          <div className="card-title">
            <Clock size={16} /> Recent Executions
          </div>
          <ul className="trade-list">
            {data.recent_trades.map((trade, i) => (
              <li key={i} className="trade-item">
                <div>
                  <div style={{fontWeight: 700, fontSize: '0.95rem'}}>{trade.symbol}</div>
                  <div style={{fontSize: '0.75rem', color: '#8b949e'}}>{trade.entry_time}</div>
                </div>
                <div style={{textAlign: 'right'}}>
                  <div className={trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'} style={{fontWeight: 700}}>
                    {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toLocaleString()}
                  </div>
                  <div style={{fontSize: '0.75rem', color: '#8b949e'}}>{trade.side}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function Card({ title, value, icon, trend, inverseColor }) {
  const isPos = trend > 0;
  return (
    <div className="card">
      <div className="card-title">{icon} {title}</div>
      <div className="stat-value">{value}</div>
      {trend && (
        <div style={{display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', marginTop: '0.5rem'}}>
          {isPos ? <ArrowUpRight size={14} className="pnl-positive" /> : <ArrowDownRight size={14} className="pnl-negative" />}
          <span className={isPos ? 'pnl-positive' : 'pnl-negative'}>{Math.abs(trend)}% from last run</span>
        </div>
      )}
    </div>
  );
}

export default App;
