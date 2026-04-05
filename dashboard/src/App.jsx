import { useState, useEffect, useRef, createContext, useContext, useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";
import {
  LayoutDashboard,
  TrendingUp,
  Settings,
  FlaskConical,
  History,
  Bell,
  ChevronDown,
  Play,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  BarChart2,
  Layers,
  Target,
  Shield,
  Zap,
  Download,
  Filter,
  ChevronRight,
  CircleDot,
  Activity,
  Code,
} from "lucide-react";


ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend
);

// ─── Design Tokens ───────────────────────────────────────────────────────────
const C = {
  bg: "#080c14",
  surface: "#0e1420",
  surface2: "#131d2e",
  surface3: "#182236",
  border: "#1c2d44",
  border2: "#253d5c",
  accent: "#00e5b0",
  accentDim: "#00b88a",
  accentGlow: "rgba(0,229,176,0.12)",
  blue: "#3d8bff",
  blueDim: "#1f5fd4",
  blueGlow: "rgba(61,139,255,0.12)",
  yellow: "#f5c842",
  red: "#ff4d6a",
  redGlow: "rgba(255,77,106,0.10)",
  text: "#dce8f5",
  muted: "#5f7a9a",
  muted2: "#3d5570",
};

// ─── Utility ─────────────────────────────────────────────────────────────────
function fmt(n, decimals = 2) {
  return n.toFixed(decimals);
}
function fmtPct(n) {
  return (n >= 0 ? "+" : "") + fmt(n) + "%";
}
function fmtUSD(n) {
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ─── Generate mock equity curve ───────────────────────────────────────────────
function genEquityCurve(days = 252, seed = 50) {

  const data = [1000000];
  let v = 1000000;

  let r = seed;
  for (let i = 1; i < days; i++) {
    r = (r * 1664525 + 1013904223) & 0xffffffff;
    const ret = ((r & 0xffff) / 65536 - 0.49) * 0.022;
    v *= 1 + ret;
    data.push(Math.round(v));
  }
  return data;
}

function genBenchmark(days = 252, seed = 120) {

  const data = [1000000];
  let v = 1000000;

  let r = seed;
  for (let i = 1; i < days; i++) {
    r = (r * 1664525 + 1013904223) & 0xffffffff;
    const ret = ((r & 0xffff) / 65536 - 0.493) * 0.016;
    v *= 1 + ret;
    data.push(Math.round(v));
  }
  return data;
}

function genDrawdown(equity) {
  let peak = equity[0];
  return equity.map((v) => {
    if (v > peak) peak = v;
    return ((v - peak) / peak) * 100;
  });
}

function genMonthlyReturns() {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const years = [2022, 2023, 2024];
  return years.flatMap((y) =>
    months.map((m) => {
      const r = (Math.sin(y * 31 + months.indexOf(m) * 7) * 8.5).toFixed(2);
      return { year: y, month: m, ret: parseFloat(r) };
    })
  );
}

function genTrades() {
  const syms = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "GOOG", "SPY"];
  const sides = ["LONG", "SHORT"];
  return Array.from({ length: 40 }, (_, i) => {
    const entry = 100 + Math.sin(i * 13) * 80;
    const ret = (Math.sin(i * 7 + 3) * 12).toFixed(2);
    const pnl = ((entry * 100 * parseFloat(ret)) / 100).toFixed(2);
    return {
      id: i + 1,
      sym: syms[i % syms.length],
      side: sides[i % 2],
      entry: entry.toFixed(2),
      exit: (entry * (1 + parseFloat(ret) / 100)).toFixed(2),
      ret: parseFloat(ret),
      pnl: parseFloat(pnl),
      date: `2024-${String((i % 12) + 1).padStart(2, "0")}-${String((i % 28) + 1).padStart(2, "0")}`,

      dur: `${Math.floor(Math.abs(Math.sin(i * 5)) * 14) + 1}d`,
    };
  });
}

// ─── Generate labels ──────────────────────────────────────────────────────────
function genLabels(days = 252) {
  const labels = [];
  const d = new Date("2024-01-02");
  let count = 0;
  while (count < days) {
    const day = d.getDay();
    if (day !== 0 && day !== 6) {
      labels.push(d.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
      count++;
    }
    d.setDate(d.getDate() + 1);
  }
  return labels;
}

// ─── Backtest Context & State ─────────────────────────────────────────────────

const BacktestContext = createContext({});
export const useBacktest = () => useContext(BacktestContext);

export function BacktestProvider({ children }) {
  const [config, setConfig] = useState({
    symbol: "NVDA",
    strategy: "momentum",
    startDate: "2023-01-01",
    endDate: "2024-12-31",
    leverage: 1.0,
    stopLoss: 5.0,
    takeProfit: 15.0,
    posSize: 10.0,
    customCode: `class CustomStrategy(Strategy):
    """
    Available Globals: pd, np, Strategy, MarketEvent, SignalEvent
    Class Inherits: Strategy
    """
    def __init__(self, bars, events):
        super().__init__(bars, events)
        # Initialize flags for each symbol
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                # self.bars.get_latest_bars(symbol, N=1) -> List of tuples
                bars = self.bars.get_latest_bars(s, N=1)
                
                if bars and not self.bought[s]:
                    # SignalEvent(1, symbol, time, type, strength)
                    self.events.put(SignalEvent(1, s, bars[0][0], 'LONG', 1.0))
                    self.bought[s] = True`,

    commission: 0.05

  });

  const [data, setData] = useState({
    equity: genEquityCurve(),
    benchmark: genBenchmark(),
    drawdown: genDrawdown(genEquityCurve()),
    labels: genLabels(),
    monthly: genMonthlyReturns(),
    trades: genTrades(),
    stats: null
  });


  const metrics = useMemo(() => {
    const EQUITY = data.equity || [];
    const BENCHMARK = data.benchmark || [];
    const DRAWDOWN = data.drawdown || [];
    const TRADES = data.trades || [];
    const LABELS = data.labels || [];
    const MONTHLY = data.monthly || [];

    const FINAL = EQUITY.length > 0 ? EQUITY[EQUITY.length - 1] : 1000000;
    const TOTAL_RET = ((FINAL - 1000000) / 1000000) * 100;
    const BM_FINAL = BENCHMARK.length > 0 ? BENCHMARK[BENCHMARK.length - 1] : 1000000;
    const BM_RET = ((BM_FINAL - 1000000) / 1000000) * 100;

    const MAX_DD = DRAWDOWN.length > 0 ? Math.min(...DRAWDOWN) : 0;
    const WIN_TRADES = TRADES.filter((t) => t.pnl > 0);
    const WIN_RATE = TRADES.length > 0 ? (WIN_TRADES.length / TRADES.length) * 100 : 0;
    const GROSS_PROFIT = WIN_TRADES.reduce((s, t) => s + t.pnl, 0);
    const GROSS_LOSS = Math.abs(TRADES.filter((t) => t.pnl < 0).reduce((s, t) => s + t.pnl, 0));
    const PROFIT_FACTOR = GROSS_LOSS === 0 ? (GROSS_PROFIT > 0 ? 999 : 0) : GROSS_PROFIT / GROSS_LOSS;
    const AVG_WIN = WIN_TRADES.length > 0 ? GROSS_PROFIT / WIN_TRADES.length : 0;
    const numLosses = TRADES.length - WIN_TRADES.length;
    const AVG_LOSS = numLosses > 0 ? GROSS_LOSS / numLosses : 0;

    return {
      EQUITY, BENCHMARK, DRAWDOWN, LABELS, MONTHLY, TRADES,
      FINAL, TOTAL_RET, BM_FINAL, BM_RET, MAX_DD, WIN_TRADES,
      WIN_RATE, GROSS_PROFIT, GROSS_LOSS, PROFIT_FACTOR, AVG_WIN, AVG_LOSS
    };
  }, [data]);

  return (
    <BacktestContext.Provider value={{ ...metrics, data, setData, config, setConfig }}>
      {children}
    </BacktestContext.Provider>
  );
}

// ─── Reusable primitives ──────────────────────────────────────────────────────
function Chip({ children, color = C.accent }) {
  return (
    <span
      style={{
        background: color + "18",
        color,
        border: `1px solid ${color}28`,
        borderRadius: 4,
        padding: "2px 8px",
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
        fontWeight: 600,
        letterSpacing: "0.04em",
      }}
    >
      {children}
    </span>
  );
}

function StatCard({ label, value, sub, subUp, icon: Icon, accent = C.accent, small = false }) {
  return (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 8,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: 80, background: accent + "08", borderRadius: "0 12px 0 80px", pointerEvents: "none" }} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <span style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600 }}>{label}</span>
        {Icon && (
          <div style={{ background: accent + "15", borderRadius: 8, padding: 6, display: "flex" }}>
            <Icon size={14} color={accent} />
          </div>
        )}
      </div>
      <div style={{ fontSize: small ? 22 : 28, fontWeight: 700, color: C.text, fontFamily: "'JetBrains Mono', monospace", lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
          {subUp !== undefined &&
            (subUp ? <ArrowUpRight size={12} color={C.accent} /> : <ArrowDownRight size={12} color={C.red} />)}
          <span style={{ color: subUp === undefined ? C.muted : subUp ? C.accent : C.red }}>{sub}</span>
        </div>
      )}
    </div>
  );
}

function SectionTitle({ children, action }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
      <h2 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: C.muted, textTransform: "uppercase", letterSpacing: "0.1em" }}>
        {children}
      </h2>
      {action}
    </div>
  );
}

function IconBtn({ icon: Icon, onClick, label }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onClick}
      title={label}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover ? C.surface3 : "transparent",
        border: `1px solid ${hover ? C.border2 : C.border}`,
        borderRadius: 8,
        padding: "6px 8px",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        gap: 6,
        color: hover ? C.text : C.muted,
        fontSize: 12,
        transition: "all 0.15s",
      }}
    >
      <Icon size={13} />
      {label && <span>{label}</span>}
    </button>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", id: "dashboard" },
  { icon: Code, label: "Custom Strategy", id: "custom" },
  { icon: FlaskConical, label: "Strategies", id: "strategies" },
  { icon: TrendingUp, label: "Results", id: "results" },
  { icon: History, label: "History", id: "history" },
  { icon: BarChart2, label: "Analytics", id: "analytics" },
  { icon: Settings, label: "Settings", id: "settings" },
];


function Sidebar({ active, setActive }) {
  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        background: C.surface,
        borderRight: `1px solid ${C.border}`,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        position: "sticky",
        top: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: "22px 20px 18px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, background: `linear-gradient(135deg, ${C.accent}, ${C.blue})`, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Activity size={16} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: C.text, letterSpacing: "-0.02em" }}>NexusQuant</div>
            <div style={{ fontSize: 10, color: C.muted, letterSpacing: "0.08em" }}>BACKTESTING</div>
          </div>
        </div>
      </div>

      {/* Strategy pill */}
      <div style={{ padding: "14px 12px 0" }}>
        <div style={{ background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 12px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 2 }}>Active Strategy</div>
            <div style={{ fontSize: 13, color: C.text, fontWeight: 600 }}>Momentum Alpha</div>
          </div>
          <ChevronDown size={14} color={C.muted} />
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 12px", display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map(({ icon: Icon, label, id }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => setActive(id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "9px 12px",
                borderRadius: 8,
                border: "none",
                background: isActive ? C.accentGlow : "transparent",
                cursor: "pointer",
                color: isActive ? C.accent : C.muted,
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                width: "100%",
                textAlign: "left",
                transition: "all 0.15s",
                outline: "none",
              }}
            >
              <Icon size={15} />
              {label}
              {isActive && <ChevronRight size={12} style={{ marginLeft: "auto" }} />}
            </button>
          );
        })}
      </nav>

      {/* Bottom status */}
      <div style={{ padding: "14px 12px", borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: C.surface3, borderRadius: 8 }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: C.accent, boxShadow: `0 0 6px ${C.accent}` }} />
          <span style={{ fontSize: 11, color: C.muted }}>Engine Ready</span>
          <Chip color={C.accent}>v2.4.1</Chip>
        </div>
      </div>
    </aside>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar({ running, onRun }) {
  const { config, setConfig } = useBacktest();

  return (
    <header
      style={{
        height: 56,
        background: C.surface,
        borderBottom: `1px solid ${C.border}`,
        display: "flex",
        alignItems: "center",
        padding: "0 24px",
        gap: 14,
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}
    >
      {/* Date range */}
      <div style={{ display: "flex", gap: 8, flex: 1, alignItems: "center" }}>
        <input
          value={config.symbol}
          onChange={(e) => setConfig({ ...config, symbol: e.target.value.toUpperCase() })}
          placeholder="Ticker"
          style={{
            background: C.surface3,
            border: `1px solid ${C.border}`,
            borderRadius: 7,
            padding: "5px 12px",
            fontSize: 13,
            color: C.text,
            width: 70,
            fontFamily: "'JetBrains Mono', monospace",
            textTransform: "uppercase",
            outline: "none"
          }}
        />
        <span style={{ fontSize: 12, color: C.muted, marginLeft: 8 }}>Period</span>
        {[config.startDate, config.endDate].map((d, i) => (
          <input
            key={i}
            type="date"
            value={d}
            onChange={(e) => {
               const key = i === 0 ? "startDate" : "endDate";
               setConfig({ ...config, [key]: e.target.value });
            }}
            style={{
              background: C.surface3,
              border: `1px solid ${C.border}`,
              borderRadius: 7,
              padding: "5px 12px",
              fontSize: 12,
              color: C.text,
              fontFamily: "'JetBrains Mono', monospace",
              cursor: "pointer",
            }}
          />
        ))}
        <span style={{ fontSize: 12, color: C.muted, marginLeft: 8 }}>vs</span>
        <div style={{ background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 7, padding: "5px 12px", fontSize: 12, color: C.muted, cursor: "pointer" }}>
          SPY (Benchmark)
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <IconBtn icon={Filter} label="Filters" />
        <IconBtn icon={Download} label="Export" />
        <button
          onClick={onRun}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 18px",
            background: running ? C.accentDim : C.accent,
            border: "none",
            borderRadius: 8,
            cursor: "pointer",
            color: "#000",
            fontWeight: 700,
            fontSize: 13,
            transition: "all 0.2s",
            letterSpacing: "0.02em",
          }}
        >
          {running ? <RefreshCw size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={14} />}
          {running ? "Running…" : "Run Backtest"}
        </button>
        <div style={{ width: 1, height: 28, background: C.border, margin: "0 4px" }} />
        <div style={{ position: "relative", cursor: "pointer" }}>
          <Bell size={17} color={C.muted} />
          <div style={{ position: "absolute", top: -2, right: -2, width: 6, height: 6, borderRadius: "50%", background: C.accent }} />
        </div>
        <div style={{ width: 30, height: 30, borderRadius: "50%", background: `linear-gradient(135deg, ${C.blue}, ${C.accent})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: "#fff", cursor: "pointer" }}>
          AG
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </header>
  );
}

// ─── Equity Chart ─────────────────────────────────────────────────────────────
function EquityChart() {
  const { LABELS, EQUITY, BENCHMARK } = useBacktest();
  const stride = 5;
  const labels = LABELS.filter((_, i) => i % stride === 0);
  const eq = EQUITY.filter((_, i) => i % stride === 0);
  const bm = BENCHMARK.filter((_, i) => i % stride === 0);

  const data = {
    labels,
    datasets: [
      {
        label: "Strategy",
        data: eq,
        borderColor: C.accent,
        backgroundColor: C.accent + "14",
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      },
      {
        label: "Benchmark",
        data: bm,
        borderColor: C.blue + "80",
        backgroundColor: "transparent",
        fill: false,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 1.5,
        borderDash: [5, 4],
      },
    ],
  };

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: C.surface2,
        borderColor: C.border2,
        borderWidth: 1,
        titleColor: C.muted,
        bodyColor: C.text,
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${fmtUSD(ctx.raw)}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: C.muted, font: { size: 10, family: "'JetBrains Mono', monospace" }, maxTicksLimit: 8 },
        grid: { color: C.border + "60" },
        border: { color: C.border },
      },
      y: {
        ticks: {
          color: C.muted,
          font: { size: 10, family: "'JetBrains Mono', monospace" },
          callback: (v) => "$" + (v / 1000).toFixed(0) + "k",
        },
        grid: { color: C.border + "60" },
        border: { color: C.border },
      },
    },
  };

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px 20px 16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <SectionTitle>Equity Curve</SectionTitle>
          <div style={{ display: "flex", gap: 18, marginTop: -8 }}>
            {[
              { label: "Strategy", color: C.accent },
              { label: "Benchmark (SPY)", color: C.blue, dashed: true },
            ].map(({ label, color, dashed }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.muted }}>
                <div style={{
                  width: 22, height: 2,
                  background: dashed ? "transparent" : color,
                  borderTop: dashed ? `2px dashed ${color}80` : "none",
                }} />
                {label}
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {["1M", "3M", "6M", "YTD", "1Y", "ALL"].map((t) => (
            <button
              key={t}
              style={{
                background: t === "1Y" ? C.accentGlow : "transparent",
                border: `1px solid ${t === "1Y" ? C.accentDim : C.border}`,
                borderRadius: 6,
                padding: "4px 10px",
                fontSize: 11,
                color: t === "1Y" ? C.accent : C.muted,
                cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div style={{ height: 260, position: "relative" }}>
        <Line data={data} options={opts} />
      </div>
    </div>
  );
}

// ─── Drawdown Chart ───────────────────────────────────────────────────────────
function DrawdownChart() {
  const { LABELS, DRAWDOWN } = useBacktest();
  const stride = 5;
  const labels = LABELS.filter((_, i) => i % stride === 0);
  const dd = DRAWDOWN.filter((_, i) => i % stride === 0);

  const data = {
    labels,
    datasets: [
      {
        label: "Drawdown",
        data: dd,
        borderColor: C.red,
        backgroundColor: C.red + "20",
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 1.5,
      },
    ],
  };

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: C.surface2,
        borderColor: C.border2,
        borderWidth: 1,
        titleColor: C.muted,
        bodyColor: C.red,
        callbacks: { label: (ctx) => ` DD: ${ctx.raw.toFixed(2)}%` },
      },
    },
    scales: {
      x: { ticks: { color: C.muted, font: { size: 10, family: "'JetBrains Mono', monospace" }, maxTicksLimit: 8 }, grid: { color: C.border + "60" }, border: { color: C.border } },
      y: {
        ticks: { color: C.muted, font: { size: 10, family: "'JetBrains Mono', monospace" }, callback: (v) => v.toFixed(1) + "%" },
        grid: { color: C.border + "60" },
        border: { color: C.border },
      },
    },
  };

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px 20px 16px" }}>
      <SectionTitle>Drawdown</SectionTitle>
      <div style={{ height: 150, position: "relative" }}>
        <Line data={data} options={opts} />
      </div>
    </div>
  );
}

// ─── Monthly Returns Heatmap ──────────────────────────────────────────────────
function MonthlyHeatmap() {
  const { MONTHLY } = useBacktest();
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const years = [2022, 2023, 2024];

  function cellColor(ret) {
    if (ret > 5) return { bg: C.accent + "40", text: C.accent };
    if (ret > 2) return { bg: C.accent + "22", text: C.accentDim };
    if (ret > 0) return { bg: C.accent + "10", text: C.accent + "aa" };
    if (ret > -2) return { bg: C.red + "10", text: C.red + "aa" };
    if (ret > -5) return { bg: C.red + "22", text: C.red };
    return { bg: C.red + "40", text: C.red };
  }

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px" }}>
      <SectionTitle>Monthly Returns</SectionTitle>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 11 }}>
          <thead>
            <tr>
              <th style={{ padding: "4px 8px", color: C.muted, textAlign: "left", fontWeight: 500 }}>Year</th>
              {months.map((m) => (
                <th key={m} style={{ padding: "4px 6px", color: C.muted, fontWeight: 500, minWidth: 44 }}>{m}</th>
              ))}
              <th style={{ padding: "4px 8px", color: C.muted, fontWeight: 500 }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {years.map((y) => {
              const rows = MONTHLY.filter((d) => d.year === y);
              const total = rows.reduce((s, d) => s + d.ret, 0);
              return (
                <tr key={y}>
                  <td style={{ padding: "4px 8px", color: C.text, fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>{y}</td>
                  {rows.map(({ month, ret }) => {
                    const { bg, text } = cellColor(ret);
                    return (
                      <td key={month} style={{ padding: 3 }}>
                        <div
                          style={{
                            background: bg,
                            borderRadius: 5,
                            padding: "5px 0",
                            textAlign: "center",
                            color: text,
                            fontFamily: "'JetBrains Mono', monospace",
                            fontSize: 11,
                            fontWeight: 600,
                          }}
                        >
                          {ret > 0 ? "+" : ""}{ret.toFixed(1)}%
                        </div>
                      </td>
                    );
                  })}
                  <td style={{ padding: "4px 8px" }}>
                    <div
                      style={{
                        color: total >= 0 ? C.accent : C.red,
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 12,
                        fontWeight: 700,
                      }}
                    >
                      {total >= 0 ? "+" : ""}{total.toFixed(1)}%
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Trade Log ────────────────────────────────────────────────────────────────
function TradeLog() {
  const { TRADES } = useBacktest();
  const [sort, setSort] = useState("date");
  const [filter, setFilter] = useState("ALL");

  const visible = TRADES.filter((t) => filter === "ALL" || t.side === filter)
    .sort((a, b) => {
      if (sort === "pnl") return b.pnl - a.pnl;
      if (sort === "ret") return b.ret - a.ret;
      return b.id - a.id;
    })
    .slice(0, 15);

  const cols = ["#", "Symbol", "Side", "Entry", "Exit", "Return", "P&L", "Date", "Dur"];

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <h2 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: C.muted, textTransform: "uppercase", letterSpacing: "0.1em" }}>Trade Log</h2>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {["ALL", "LONG", "SHORT"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                background: filter === f ? C.accentGlow : "transparent",
                border: `1px solid ${filter === f ? C.accentDim : C.border}`,
                borderRadius: 6,
                padding: "4px 10px",
                fontSize: 11,
                color: filter === f ? C.accent : C.muted,
                cursor: "pointer",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {f}
            </button>
          ))}
          <select
            onChange={(e) => setSort(e.target.value)}
            style={{
              background: C.surface3,
              border: `1px solid ${C.border}`,
              borderRadius: 6,
              padding: "4px 8px",
              fontSize: 11,
              color: C.muted,
              cursor: "pointer",
              outline: "none",
            }}
          >
            <option value="date">Sort: Date</option>
            <option value="pnl">Sort: P&L</option>
            <option value="ret">Sort: Return</option>
          </select>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              {cols.map((c) => (
                <th
                  key={c}
                  style={{
                    padding: "8px 10px",
                    textAlign: c === "#" || c === "P&L" || c === "Return" || c === "Entry" || c === "Exit" ? "right" : "left",
                    color: C.muted,
                    fontWeight: 500,
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    whiteSpace: "nowrap",
                  }}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((t, i) => (
              <tr
                key={t.id}
                style={{
                  borderBottom: `1px solid ${C.border}40`,
                  background: i % 2 === 0 ? "transparent" : C.surface3 + "50",
                  transition: "background 0.1s",
                }}
              >
                <td style={{ padding: "9px 10px", textAlign: "right", color: C.muted2, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{t.id}</td>
                <td style={{ padding: "9px 10px", fontWeight: 600, color: C.text }}>{t.sym}</td>
                <td style={{ padding: "9px 10px" }}>
                  <Chip color={t.side === "LONG" ? C.accent : C.yellow}>{t.side}</Chip>
                </td>
                <td style={{ padding: "9px 10px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", color: C.muted }}>${t.entry}</td>
                <td style={{ padding: "9px 10px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", color: C.muted }}>${t.exit}</td>
                <td style={{ padding: "9px 10px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, color: t.ret >= 0 ? C.accent : C.red }}>
                  {fmtPct(t.ret)}
                </td>
                <td style={{ padding: "9px 10px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, color: t.pnl >= 0 ? C.accent : C.red }}>
                  {t.pnl >= 0 ? "+" : ""}{fmtUSD(t.pnl)}
                </td>
                <td style={{ padding: "9px 10px", color: C.muted, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{t.date ? t.date.split('T')[0] : "N/A"}</td>

                <td style={{ padding: "9px 10px", color: C.muted, fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{t.dur}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 12, fontSize: 12, color: C.muted, textAlign: "center" }}>
        Showing {visible.length} of {TRADES.filter((t) => filter === "ALL" || t.side === filter).length} trades
      </div>
    </div>
  );
}

// ─── Risk Metrics Panel ───────────────────────────────────────────────────────
function RiskPanel() {
  const { data } = useBacktest();
  const s = data.stats || {};
  
  const getVal = (key, fallback, suffix = "", prefix = "") => {
    const val = s[key];
    if (val === undefined || val === null) return fallback;
    return prefix + val.toLocaleString() + suffix;
  };

  const rows = [
    { label: "Sharpe Ratio", value: getVal("Sharpe Ratio", "1.84"), note: "Annualised", color: C.accent },
    { label: "Sortino Ratio", value: getVal("Sortino Ratio", "2.31"), note: "Annualised", color: C.accent },
    { label: "Calmar Ratio", value: getVal("Calmar Ratio", "3.12"), note: "Return/MaxDD", color: C.accent },
    { label: "Max Drawdown", value: getVal("Max Drawdown (%)", "5.2%", "%"), note: "Peak-to-trough", color: C.red },
    { label: "CAGR", value: getVal("CAGR (%)", "12.4%", "%"), note: "Comp. Annual Growth", color: C.accent },
    { label: "Profit Factor", value: getVal("Profit Factor", "1.65"), note: "Gross P / Gross L", color: C.accent },
    { label: "Win Rate", value: getVal("Win Rate (%)", "54.2%", "%"), note: `${getVal("Total Trades", "40")} trades`, color: C.accent },
    { label: "Avg Win", value: getVal("Avg Win", "$4,200", "", "$"), note: "Per winning trade", color: C.accent },
    { label: "Avg Loss", value: getVal("Avg Loss", "-$2,800", "", "$"), note: "Per losing trade", color: C.red },
    { label: "Expectancy", value: getVal("Expectancy", "$1,200", "", "$"), note: "Per trade", color: C.blue },
    { label: "Alpha (Ann.)", value: getVal("Alpha (Annual)", "0.045"), note: "Extra return vs BM", color: C.blue },
    { label: "Beta", value: getVal("Beta", "0.85"), note: "Sensitivity vs BM", color: C.muted },
  ];


  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px" }}>
      <SectionTitle>Risk Metrics</SectionTitle>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {rows.map(({ label, value, note, color }) => (
          <div
            key={label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "8px 10px",
              borderRadius: 6,
              borderBottom: `1px solid ${C.border}40`,
            }}
          >
            <div>
              <div style={{ fontSize: 12, color: C.text, fontWeight: 500 }}>{label}</div>
              <div style={{ fontSize: 10, color: C.muted2, marginTop: 1 }}>{note}</div>
            </div>
            <div style={{ fontSize: 14, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Strategy Config Panel ────────────────────────────────────────────────────
function StrategyPanel({ onApply, onOpenEditor }) {
  const { config, setConfig } = useBacktest();

  const slider = (label, key, min, max, step, unit) => (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 11, fontWeight: 500, color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</span>
        <span style={{ fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: C.accent, fontWeight: 600 }}>{config[key]}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={config[key]}
        onChange={(e) => setConfig({ ...config, [key]: parseFloat(e.target.value) })}
        style={{ width: "100%", accentColor: C.accent, cursor: "pointer", height: 4 }}
      />
    </div>
  );

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px", display: "flex", flexDirection: "column", gap: 20 }}>
      <SectionTitle>Strategy Config</SectionTitle>

      {/* Signal Source */}
      <div>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.05em" }}>Signal Source</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
          {["Momentum", "Mean Revert", "RSI", "MAC Cross", "Rebalance", "ML", "Multi", "Custom"].map((s) => {
            const id = s.toLowerCase().replace(" ", "_");
            const isSel = config.strategy === id;
            return (
              <button
                key={s}
                onClick={() => setConfig({ ...config, strategy: id })}
                style={{
                  padding: "8px 4px",
                  fontSize: 10,
                  background: isSel ? C.accentGlow : C.surface3,
                  border: `1px solid ${isSel ? C.accent : C.border}`,
                  borderRadius: 6,
                  color: isSel ? C.accent : C.muted,
                  cursor: "pointer",
                  fontWeight: isSel ? 600 : 400,
                  transition: "all 0.2s"
                }}
              >
                {s}
              </button>
            );
          })}
        </div>
      </div>

      {config.strategy === "custom" ? (
        <div style={{ padding: "16px", background: C.surface3, borderRadius: 10, border: `1px solid ${C.accent}40`, textAlign: "center" }}>
          <div style={{ width: 40, height: 40, background: C.accentGlow, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
            <Code size={20} color={C.accent} />
          </div>
          <div style={{ fontSize: 13, color: C.text, fontWeight: 600, marginBottom: 4 }}>Custom Logic Active</div>
          <div style={{ fontSize: 11, color: C.muted2, marginBottom: 16, lineHeight: 1.5 }}>
            Your Python strategy code is ready. Use the full-page editor for the best experience.
          </div>
          <button 
            onClick={onOpenEditor}
            style={{ 
              width: "100%", 
              background: C.surface2, 
              border: `1px solid ${C.border2}`, 
              borderRadius: 8, 
              padding: "10px", 
              fontSize: 12, 
              color: C.accent, 
              fontWeight: 600, 
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8
            }}
          >
            <Code size={14} /> Open Strategy Editor
          </button>
        </div>
      ) : (
        <>
          {slider("Leverage", "leverage", 1, 5, 0.1, "x")}
          {slider("Stop Loss", "stopLoss", 1, 20, 0.5, "%")}
          {slider("Take Profit", "takeProfit", 1, 50, 0.5, "%")}
          {slider("Position Size", "posSize", 1, 100, 1, "%")}
          {slider("Commission", "commission", 0, 0.5, 0.01, "%")}
        </>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button 
          onClick={() => setConfig({ ...config, leverage: 1.0, stopLoss: 5.0, takeProfit: 15.0, posSize: 10.0, commission: 0.05 })}
          style={{ flex: 1, background: C.surface3, border: `1px solid ${C.border}`, borderRadius: 8, padding: "9px", fontSize: 12, color: C.muted, cursor: "pointer" }}
        >
          Reset
        </button>
        <button onClick={onApply} style={{ flex: 2, background: C.accent, border: "none", borderRadius: 8, padding: "9px", fontSize: 12, color: "#000", fontWeight: 700, cursor: "pointer" }}>
          Apply &amp; Rerun
        </button>
      </div>
    </div>
  );
}


// ─── Custom Strategy Editor View ─────────────────────────────────────────────
function StrategyEditorView({ onRun, running }) {
  const { config, setConfig } = useBacktest();

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 56px)", background: C.bg }}>
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Editor Area */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: 20, borderRight: `1px solid ${C.border}` }}>
          <SectionTitle 
            action={
              <button
                onClick={onRun}
                disabled={running}
                style={{
                  padding: "6px 16px",
                  background: running ? C.accentDim : C.accent,
                  border: "none",
                  borderRadius: 6,
                  color: "#000",
                  fontWeight: 600,
                  fontSize: 12,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6
                }}
              >
                {running ? <RefreshCw size={12} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={12} />}
                {running ? "Running..." : "Save & Run Backtest"}
              </button>
            }
          >
            Strategy Implementation (Python)
          </SectionTitle>
          <textarea
            value={config.customCode}
            onChange={(e) => setConfig({ ...config, customCode: e.target.value })}
            spellCheck={false}
            style={{
              flex: 1,
              width: "100%",
              background: C.surface,
              color: "#cad3f5",
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: "20px",
              fontSize: 14,
              fontFamily: "'JetBrains Mono', monospace",
              resize: "none",
              outline: "none",
              lineHeight: 1.6,
              tabSize: 4
            }}
          />
        </div>

        {/* Reference Sidebar */}
        <div style={{ width: 320, padding: 20, background: C.surface, overflowY: "auto" }}>
          <SectionTitle>Variable Reference</SectionTitle>
          
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 11, color: C.accent, textTransform: "uppercase", marginBottom: 10 }}>Available Globals</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <RefCard name="pd, np" desc="Pandas and Numpy for data manipulation." />
              <RefCard name="Strategy" desc="The base class your strategy must inherit from." />
              <RefCard name="MarketEvent" desc="Event emitted for every new price bar." />
              <RefCard name="SignalEvent" desc="Event used to emit trading signals." />
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 11, color: C.accent, textTransform: "uppercase", marginBottom: 10 }}>Core Methods</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <RefCard name="get_latest_bars(sym, N)" desc="Retrieves the N most recent bars for a symbol." />
              <RefCard name="events.put(signal)" desc="Adds a new SignalEvent to the queue." />
            </div>
          </div>

          <div style={{ padding: 15, background: C.surface3, borderRadius: 8, border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 600, marginBottom: 6 }}>Pro Tip:</div>
            <div style={{ fontSize: 11, color: C.muted2, lineHeight: 1.5 }}>
              Use <code style={{ color: C.text }}>'LONG'</code> to buy and <code style={{ color: C.text }}>'EXIT'</code> to close positions. Stay consistent with your symbol list.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RefCard({ name, desc }) {
  return (
    <div style={{ padding: "10px 12px", background: C.surface3, borderRadius: 6, border: `1px solid ${C.border}` }}>
      <code style={{ fontSize: 12, color: C.text, display: "block", marginBottom: 4 }}>{name}</code>
      <div style={{ fontSize: 11, color: C.muted2, lineHeight: 1.4 }}>{desc}</div>
    </div>
  );
}

// ─── Distribution Chart ───────────────────────────────────────────────────────

function DistributionChart() {
  const bins = Array.from({ length: 20 }, (_, i) => ({
    label: `${(i - 10) * 2}%`,
    val: Math.round(Math.abs(Math.sin(i * 2.3 + 1) * 8)) + (i > 8 && i < 13 ? 6 : 0),
  }));

  const colors = bins.map((b) => (parseInt(b.label) >= 0 ? C.accent + "cc" : C.red + "cc"));

  const data = {
    labels: bins.map((b) => b.label),
    datasets: [{ label: "Trades", data: bins.map((b) => b.val), backgroundColor: colors, borderRadius: 3, borderSkipped: false }],
  };

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { backgroundColor: C.surface2, borderColor: C.border2, borderWidth: 1, bodyColor: C.text } },
    scales: {
      x: { ticks: { color: C.muted, font: { size: 9, family: "'JetBrains Mono', monospace" }, maxTicksLimit: 10 }, grid: { display: false }, border: { color: C.border } },
      y: { ticks: { color: C.muted, font: { size: 10, family: "'JetBrains Mono', monospace" } }, grid: { color: C.border + "50" }, border: { color: C.border } },
    },
  };

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "20px" }}>
      <SectionTitle>Return Distribution</SectionTitle>
      <div style={{ height: 180, position: "relative" }}>
        <Bar data={data} options={opts} />
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
function DashboardContent() {
  const [active, setActive] = useState("dashboard");
  const [running, setRunning] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [progress, setProgress] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");
  
  const { TOTAL_RET, BM_RET, FINAL, MAX_DD, WIN_RATE, PROFIT_FACTOR, TRADES, WIN_TRADES, data, setData, config } = useBacktest();



  async function handleRun() {
    setRunning(true);
    setShowProgress(true);
    setLoadingMsg(`Fetching ${config.symbol} Data...`);
    setProgress(15);
    try {
      const formData = new FormData();
      formData.append("symbol", config.symbol);
      formData.append("strategy", config.strategy);
      formData.append("startDate", config.startDate);
      formData.append("endDate", config.endDate);
      formData.append("leverage", config.leverage);
      formData.append("stopLoss", config.stopLoss);
      formData.append("takeProfit", config.takeProfit);
      formData.append("posSize", config.posSize);
      formData.append("commission", config.commission);
      formData.append("customCode", config.customCode);


      const res = await fetch("http://localhost:8000/backtest", {
        method: "POST",
        body: formData,
      });
      const result = await res.json();
      
      if (result.error) {
        alert(result.error);
        setProgress(100);
        return;
      }

      setLoadingMsg("Running Simulation...");
      setProgress(60);


      if (result && result.charts) {
        const capital = result.metadata?.initial_capital || 1000000;
        const labels = result.charts.map(c => c.date);
        const equity = result.charts.map(c => c.equity * capital);
        const benchmark = result.charts.map(c => (c.benchmark || 1.0) * capital);
        const drawdown = result.charts.map(c => c.drawdown * 100);
        
        const mappedTrades = (result.recent_trades || []).map((t, i) => {
           let durMatch = (t.duration || "").toString().match(/\d+/);
           let dur = durMatch ? durMatch[0] + "d" : "1d";
           let entryDate = t.entry_time || "N/A";
           let exitDate = t.exit_time || entryDate;
           
           return {
             id: i + 1,
             sym: t.symbol,
             side: t.side,
             entry: (t.entry_price || 0).toFixed(2),
             exit: (t.exit_price || 0).toFixed(2),
             ret: t.pnl_pct || 0,
             pnl: t.pnl || 0,
             date: exitDate.split("T")[0],
             dur: dur
           };
        });

        setData(prev => ({
          ...prev,
          labels,
          equity,
          benchmark,
          drawdown,
          trades: mappedTrades,
          stats: result.stats || null
        }));
      }

      setProgress(100);
    } catch (err) {
      console.error("Backtest Error:", err);
      setProgress(100);
    } finally {
      setTimeout(() => {
        setRunning(false);
        setShowProgress(false);
      }, 500);
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@400;500;600;700&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${C.bg}; color: ${C.text}; font-family: 'Outfit', sans-serif; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: ${C.surface}; }
        ::-webkit-scrollbar-thumb { background: ${C.border2}; border-radius: 3px; }
        input[type=range] { -webkit-appearance: none; height: 4px; background: ${C.border2}; border-radius: 2px; outline: none; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: ${C.accent}; cursor: pointer; }
        select { -webkit-appearance: none; }
        button { font-family: 'Outfit', sans-serif; }
        tr:hover { background: ${C.surface3} !important; }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>
        <Sidebar active={active} setActive={setActive} />

        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          <TopBar running={running} onRun={handleRun} />

          {/* Progress bar */}
          {showProgress && (
            <div style={{ position: "relative", height: 20, background: C.border, display: "flex", alignItems: "center" }}>
              <div style={{ position: "absolute", height: "100%", width: `${Math.min(progress, 100)}%`, background: C.accentGlow, transition: "width 0.15s" }} />
              <div style={{ position: "absolute", bottom: 0, height: 2, width: `${Math.min(progress, 100)}%`, background: C.accent, transition: "width 0.15s" }} />
              <span style={{ position: "relative", zIndex: 1, fontSize: 10, color: C.accent, fontWeight: 700, marginLeft: 24, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {loadingMsg}
              </span>
            </div>
          )}


          <main style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", background: active === "custom" ? C.bg : "transparent" }}>
            {active === "custom" ? (
              <StrategyEditorView onRun={handleRun} running={running} />
            ) : (
              <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
                {/* KPI Row */}
                {(active === "dashboard" || active === "results" || active === "analytics") && (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
                    <StatCard label="Total Return" value={fmtPct(TOTAL_RET)} sub={`vs BM ${fmtPct(BM_RET)}`} subUp={TOTAL_RET > BM_RET} icon={TrendingUp} accent={C.accent} />
                    <StatCard label="Sharpe Ratio" value={data.stats ? data.stats["Sharpe Ratio"] : "1.84"} sub="Risk-adjusted return" subUp={true} icon={Zap} accent={C.blue} />
                    <StatCard label="Max Drawdown" value={data.stats ? data.stats["Max Drawdown (%)"] + "%" : fmt(Math.abs(MAX_DD), 2) + "%"} sub="Peak-to-trough" subUp={false} icon={Shield} accent={C.red} />
                    <StatCard label="Win Rate" value={data.stats ? data.stats["Win Rate (%)"] + "%" : fmt(WIN_RATE, 1) + "%"} sub={`${data.stats ? data.stats["Total Trades"] : TRADES.length} trades`} subUp icon={Target} accent={C.accent} />
                    <StatCard label="Profit Factor" value={data.stats ? data.stats["Profit Factor"] : fmt(PROFIT_FACTOR)} sub="Gross P/L ratio" subUp icon={Layers} accent={C.yellow} />
                    <StatCard label="Final Equity" value={"$" + (FINAL / 1000).toFixed(1) + "k"} sub={`+${fmtUSD(FINAL - 100000)} profit`} subUp icon={CircleDot} accent={C.blue} />
                  </div>
                )}


                {/* Charts + Config */}
                {(active === "dashboard" || active === "strategies" || active === "results") && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16 }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                       <EquityChart />
                       <DrawdownChart />
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                       <StrategyPanel onApply={handleRun} onOpenEditor={() => setActive("custom")} />
                    </div>
                  </div>
                )}

                {/* Monthly + Distribution */}
                {(active === "dashboard" || active === "analytics") && (
                  <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
                    <MonthlyHeatmap />
                    <DistributionChart />
                  </div>
                )}

                {/* Trade Log + Risk */}
                {(active === "dashboard" || active === "history") && (
                  <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16 }}>
                    <TradeLog />
                    <RiskPanel />
                  </div>
                )}
              </div>
            )}
          </main>

        </div>
      </div>
    </>
  );
}

export default function App() {
  return (
    <BacktestProvider>
      <DashboardContent />
    </BacktestProvider>
  );
}
