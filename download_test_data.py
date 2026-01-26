#!/usr/bin/env python
"""One-liner to download AAPL data for testing"""
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Create data directory
os.makedirs('data', exist_ok=True)

# Download AAPL data (3 years)
print("📥 Downloading AAPL data (3 years)...")
end_date = datetime.now()
start_date = end_date - timedelta(days=365*3)

ticker = yf.Ticker('AAPL')
df = ticker.history(start=start_date, end=end_date)

# Format data
df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
df = df[['open', 'high', 'low', 'close', 'volume']]
df.reset_index(inplace=True)
df = df.rename(columns={'Date': 'datetime'})
df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d')

# Save to CSV
output_file = 'data/AAPL.csv'
df.to_csv(output_file, index=False)

print(f"✅ Downloaded {len(df)} rows")
print(f"📁 Saved to: {output_file}")
print(f"📊 Date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
print("\n📋 Preview:")
print(df.head(10))
print(f"\n... ({len(df)} total rows)")
