import React, { useState, useEffect } from 'react';
import { 
  LineChart, TrendingUp, Activity, Shield, 
  ArrowUpRight, ArrowDownRight, RefreshCcw, 
  BarChart3, Clock, LayoutDashboard, DollarSign, Percent, Zap
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
  const defaultCustomCode = `class CustomStrategy(Strategy):
    """
    Docs:
    - self.bars.get_latest_bar_value(symbol, 'close')
    - self.bars.get_latest_bars(symbol, N)
    - self._generate_signal(symbol, 'LONG' / 'SHORT' / 'EXIT')
    """
    def __init__(self, bars, events, **kwargs):
        super().__init__(bars, events)
        self.period = 14
        
    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, self.period)
                if len(bars) < self.period: return
                
                close = self.bars.get_latest_bar_value(s, 'close')
                
                # A simple breakout logic
                if close > 150:
                    self._generate_signal(s, 'LONG')
`;
  const [strategy, setStrategy] = useState('multi');
  const [symbol, setSymbol] = useState('NVDA');
  const [customCode, setCustomCode] = useState(defaultCustomCode);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  const runBacktest = async (e) => {
    if (e) e.preventDefault();
    setIsRunning(true);
    
    const formData = new FormData();
    formData.append('strategy', strategy);
    formData.append('symbol', symbol);
    if (strategy === 'custom') {
      formData.append('customCode', customCode);
    }

    setErrorMsg(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/backtest', {
        method: 'POST',
        body: formData
      });
      const json = await response.json();
      
      if (json.error) {
        setErrorMsg(json.error + (json.traceback ? '\\n' + json.traceback : ''));
        setLoading(false);
        setIsRunning(false);
        return;
      }
      
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
        titleColor: '#09b1a9ff',
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
    labels: data?.charts?.map(d => d.date) || [],
    datasets: [
      {
        label: 'Strategy Equity',
        data: data?.charts?.map(d => d.equity) || [],
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88, 166, 255, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Benchmark',
        data: data?.charts?.map(d => d.benchmark) || [],
        borderColor: '#8b949e',
        borderDash: [5, 5],
        fill: false,
        tension: 0.4
      }
    ]
  };

  const formatValue = (key, val) => {
    if (val === null || val === undefined || val === 'N/A' || isNaN(val)) return val;
    const num = Number(val);
    if (key.includes('Equity') || key.includes('PnL') || key === 'Avg Win' || key === 'Avg Loss' || key.includes('Commissions')) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num);
    }
    if (key.includes('(%)') || key.includes('Rate')) {
        return `${num.toFixed(2)}%`;
    }
    if (num % 1 !== 0) return num.toFixed(2);
    return num.toLocaleString();
  };

  const getIcon = (key) => {
    if (key.includes('Equity') || key.includes('PnL') || key.includes('Win') || key.includes('Profit')) return <DollarSign size={16} className="text-primary" />;
    if (key.includes('Ratio') || key.includes('Drawdown') || key.includes('Risk') || key.includes('Streak')) return <Shield size={16} className="text-secondary" />;
    if (key.includes('Current') || key.includes('MACD') || key.includes('RSI')) return <Activity size={16} className="text-accent" />;
    if (key.includes('%') || key.includes('Rate')) return <Percent size={16} className="text-primary" />;
    if (key.includes('Time') || key.includes('Duration')) return <Clock size={16} className="text-muted" />;
    return <Zap size={16} className="text-muted" />;
  };

  const heroKeys = ['Final Equity', 'CAGR (%)', 'Sharpe Ratio', 'Max Drawdown (%)'];


  return (
    <div className="dashboard-container">
      <header className="header">
        <div className="brand">
          <h1>ANTIGRAVITY <span style={{color: '#8b949e', fontWeight: 300}}>ENGINE</span></h1>
          <p style={{color: '#8b949e', fontSize: '0.8rem'}}>Advanced Event-Driven Backtesting v2.0</p>
        </div>
        
        <div style={{display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap'}}>
          <input 
            type="text" 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Symbol (e.g. NVDA)"
            style={{background: 'var(--card-bg)', color: 'var(--text-color)', border: '1px solid var(--border-color)', padding: '8px 12px', borderRadius: '8px', width: '100px'}}
          />

          <select 
            value={strategy} 
            onChange={(e) => setStrategy(e.target.value)}
            style={{background: 'var(--card-bg)', color: 'var(--text-color)', border: '1px solid var(--border-color)', padding: '8px 12px', borderRadius: '8px', cursor: 'pointer', maxWidth: '300px'}}
          >
            <option value="multi">Advanced Multi-Strategy (Regime Gated)</option>
            <option value="momentum">Momentum Strategy</option>
            <option value="mean_reversion">Mean Reversion</option>
            <option value="rsi">RSI Strategy</option>
            <option value="mac">Moving Average Crossover</option>
            <option value="rebalance">Monthly Rebalancing</option>
            <option value="custom">Write Custom Python Strategy...</option>
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
            <span style={{fontSize: '0.85rem', fontWeight: 600}}>{isRunning ? 'Processing...' : (data?.stats ? 'System Idle' : 'Ready')}</span>
          </div>
        </div>
      </header>

      {errorMsg && (
        <div style={{background: 'rgba(248, 81, 73, 0.1)', border: '1px solid #f85149', color: '#f85149', padding: '1rem', margin: '1rem 0', borderRadius: '8px', fontFamily: 'monospace', whiteSpace: 'pre-wrap'}}>
          <strong>Execution Error:</strong><br />
          {errorMsg}
        </div>
      )}

      {strategy === 'custom' && (
        <div className="card" style={{marginBottom: '1.5rem'}}>
          <div className="card-title" style={{marginBottom: '0.5rem'}}>Python Strategy Editor (Write 'CustomStrategy' class)</div>
          <textarea 
            value={customCode}
            onChange={(e) => setCustomCode(e.target.value)}
            spellCheck="false"
            style={{
              width: '100%', minHeight: '300px', background: '#0d1117', color: '#c9d1d9',
              fontFamily: 'monospace', padding: '12px', borderRadius: '8px', 
              border: '1px solid #30363d', resize: 'vertical'
            }}
          />
        </div>
      )}

      <div className="stats-grid-hero">
        {data?.stats && heroKeys.map(k => (
          data.stats[k] !== undefined && <HeroCard key={k} title={k} value={formatValue(k, data.stats[k])} icon={getIcon(k)} />
        ))}
      </div>

      <div className="stats-grid-secondary">
        {data?.stats && Object.entries(data.stats)
          .filter(([k, v]) => !heroKeys.includes(k))
          .map(([k, v]) => (
            <Card key={k} title={k} value={formatValue(k, v)} icon={getIcon(k)} />
        ))}
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
            {data?.recent_trades?.map((trade, i) => (
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
      <div className="card-title">{icon} <span style={{whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{title}</span></div>
      <div className="stat-value" style={{fontSize: '1.4rem'}}>{value}</div>
      {trend && (
        <div style={{display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem', marginTop: '0.5rem'}}>
          {isPos ? <ArrowUpRight size={14} className="pnl-positive" /> : <ArrowDownRight size={14} className="pnl-negative" />}
          <span className={isPos ? 'pnl-positive' : 'pnl-negative'}>{Math.abs(trend)}% from last run</span>
        </div>
      )}
    </div>
  );
}

function HeroCard({ title, value, icon }) {
  return (
    <div className="card hero-card">
      <div className="card-title" style={{color: '#fff'}}>{icon} {title}</div>
      <div className="stat-value hero-value">{value}</div>
    </div>
  );
}

export default App;
