# 📥 How to Download CSV Data for Backtesting

## ✅ DONE! Sample Data Already Downloaded

I've already downloaded **AAPL stock data (3 years, 751 rows)** for you!

**Location:** `/Users/shreyanshsingh/mp_env/data/AAPL.csv`

You can start backtesting right away! 🎉

---

## 📊 What's in the CSV File?

Your CSV file has the required format:

```csv
datetime,open,high,low,close,volume
2023-01-26,141.04,142.11,139.79,141.82,54105100
2023-01-27,141.03,145.04,140.95,143.76,70555800
...
```

This matches exactly what your `HistoricCSVDataHandler` expects!

---

## 🚀 Quick Start - Run Your First Backtest!

Now that you have data, you can run a backtest:

```bash
cd /Users/shreyanshsingh/mp_env
source bin/activate
python complete_backtest_system.py
```

Or modify `complete_backtest_system.py` at the bottom:

```python
# Configuration
csv_dir = '/Users/shreyanshsingh/mp_env/data'  # ✅ Already correct
symbol_list = ['AAPL']  # ✅ AAPL data is ready
initial_capital = 100000.0
heartbeat = 0.0
start_date = datetime.datetime(2023, 1, 26)  # Match your data start date
```

---

## 📥 Download More Stocks

I've created 3 scripts for downloading more data:

### Option 1: Super Simple (Recommended)
```bash
source bin/activate
python download_test_data.py
```

This downloads AAPL data (3 years) - **Already done for you!**

---

### Option 2: Interactive Menu
```bash
source bin/activate
python quick_download.py
```

**Available options:**
1. Quick Download - Single Stock (AAPL, 3 years)
2. Download Tech Stocks (AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA)
3. Download Dow Stocks (10 major stocks)
4. Custom Download (Choose your own stocks)
5. Quick Test (AAPL, 1 year)

---

### Option 3: Advanced Script
```bash
source bin/activate
python download_stock_data.py
```

Edit the script to customize:
```python
symbols = ['AAPL', 'MSFT', 'GOOGL']  # Your stocks
start_date = '2020-01-01'
end_date = '2023-12-31'
```

---

## 📝 Custom Download Example

Want to download specific stocks? Here's a quick Python snippet:

```python
import yfinance as yf
import pandas as pd

# Download Tesla data
ticker = yf.Ticker('TSLA')
df = ticker.history(start='2020-01-01', end='2023-12-31')

# Format for backtesting
df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
df = df[['open', 'high', 'low', 'close', 'volume']]
df.reset_index(inplace=True)
df = df.rename(columns={'Date': 'datetime'})
df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d')

# Save
df.to_csv('data/TSLA.csv', index=False)
print(f"✅ Downloaded {len(df)} rows to data/TSLA.csv")
```

---

## 🔍 Popular Stock Symbols

### Tech Giants
- **AAPL** - Apple ✅ (Already downloaded!)
- **MSFT** - Microsoft
- **GOOGL** - Google
- **AMZN** - Amazon
- **META** - Meta (Facebook)
- **NVDA** - NVIDIA
- **TSLA** - Tesla

### Finance
- **JPM** - JPMorgan Chase
- **V** - Visa
- **MA** - Mastercard
- **GS** - Goldman Sachs

### Indices (ETFs)
- **SPY** - S&P 500 ETF
- **QQQ** - NASDAQ-100 ETF
- **DIA** - Dow Jones ETF
- **IWM** - Russell 2000 ETF

---

## 📂 File Structure

After downloading, your structure should look like:

```
/Users/shreyanshsingh/mp_env/
├── data/
│   ├── AAPL.csv ✅ (Already exists!)
│   ├── MSFT.csv (Download if needed)
│   └── GOOGL.csv (Download if needed)
├── complete_backtest_system.py
├── download_test_data.py
├── quick_download.py
└── download_stock_data.py
```

---

## ⚠️ Important Notes

### Data Source
All scripts use **Yahoo Finance** (free, no API key needed)

### Date Range
- Recommended: 2-5 years of data
- Your AAPL data: **Jan 26, 2023 to Jan 23, 2026** (3 years, 751 trading days)

### CSV Format
The backtesting system requires this exact format:
```csv
datetime,open,high,low,close,volume
```

All my scripts generate this format automatically ✅

### Time Zone
All timestamps are in UTC/EST (market time)

---

## 🧪 Test Your Setup

Quick test to verify everything works:

```bash
cd /Users/shreyanshsingh/mp_env
source bin/activate

# 1. Check if data exists
ls -lh data/AAPL.csv

# 2. Preview the data
head -10 data/AAPL.csv

# 3. Run a backtest (if complete_backtest_system.py is ready)
python complete_backtest_system.py
```

---

## 💡 Tips

### 1. Multiple Stocks
To backtest multiple stocks, download each one:
```bash
source bin/activate
python quick_download.py
# Select option 2 for tech stocks
```

Then update your backtest:
```python
symbol_list = ['AAPL', 'MSFT', 'GOOGL']
```

### 2. Data Quality
- Yahoo Finance data is free but may have gaps
- For production, consider paid data providers (Quandl, Alpha Vantage, etc.)

### 3. Storage
- CSV files are small (50-100KB per stock per 3 years)
- Safe to download many stocks

### 4. Updates
To update data with latest prices:
```bash
source bin/activate
python download_test_data.py  # Re-downloads fresh data
```

---

## 🎯 Summary

**What you have now:**
✅ AAPL data downloaded (751 rows, 3 years)  
✅ Data in correct format for backtesting  
✅ 3 scripts to download more stocks  
✅ Everything ready to run your first backtest!

**Next steps:**
1. (Optional) Download more stocks using `quick_download.py`
2. Run your first backtest with `complete_backtest_system.py`
3. Create your own trading strategy
4. Test and refine!

---

## 🆘 Troubleshooting

### Problem: "No module named 'yfinance'"
**Solution:**
```bash
source bin/activate
pip install yfinance
```

### Problem: "No data found for symbol"
**Solution:** The ticker symbol might be wrong or delisted. Try searching on [Yahoo Finance](https://finance.yahoo.com) first.

### Problem: "Permission denied"
**Solution:**
```bash
chmod +x download_test_data.py
chmod +x quick_download.py
```

### Problem: CSV format error in backtest
**Solution:** Re-download using my scripts. They generate the exact format needed.

---

**You're all set! Happy backtesting! 🚀**
