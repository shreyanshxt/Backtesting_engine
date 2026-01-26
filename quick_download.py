#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QUICK DATA DOWNLOADER
Simple script to download stock data for backtesting
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta


def quick_download(symbols='AAPL', days=365*3, output_dir='data'):
    """
    Quick download for stock data.
    
    Parameters:
    -----------
    symbols : str or list
        Stock symbol(s) to download (default: 'AAPL')
        Examples: 'AAPL' or ['AAPL', 'MSFT', 'GOOGL']
    days : int
        Number of days of historical data (default: 1095 = 3 years)
    output_dir : str
        Where to save CSV files (default: 'data')
    """
    # Convert single symbol to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print("\n" + "="*70)
    print("📥 DOWNLOADING STOCK DATA")
    print("="*70)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Output: {output_dir}/")
    print("="*70 + "\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    success_count = 0
    
    for symbol in symbols:
        try:
            print(f"📊 Downloading {symbol}...", end=' ')
            
            # Download data
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                print("❌ No data found")
                continue
            
            # Format data
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            df = df[['open', 'high', 'low', 'close', 'volume']]
            df.reset_index(inplace=True)
            df = df.rename(columns={'Date': 'datetime'})
            df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d')
            
            # Save to CSV
            output_file = os.path.join(output_dir, f'{symbol}.csv')
            df.to_csv(output_file, index=False)
            
            print(f"✅ {len(df)} rows saved")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*70)
    print(f"✅ DOWNLOAD COMPLETE: {success_count}/{len(symbols)} successful")
    print("="*70)
    
    # Show what was downloaded
    if success_count > 0:
        print("\n📁 Files created in 'data' folder:")
        for symbol in symbols:
            file_path = os.path.join(output_dir, f'{symbol}.csv')
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✓ {symbol}.csv ({size:,} bytes)")
    
    return success_count


# =============================================================================
# PRESET CONFIGURATIONS
# =============================================================================

def download_tech_stocks():
    """Download popular tech stocks (3 years)"""
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
    quick_download(symbols, days=365*3)


def download_dow_stocks():
    """Download Dow Jones components (2 years)"""
    symbols = ['AAPL', 'MSFT', 'JPM', 'V', 'UNH', 'HD', 'PG', 'DIS', 'BA', 'MCD']
    quick_download(symbols, days=365*2)


def download_custom():
    """Download custom stocks"""
    print("\n" + "="*70)
    print("CUSTOM DOWNLOAD")
    print("="*70)
    
    # Get user input
    symbols_input = input("\nEnter stock symbols (comma-separated, e.g., AAPL,MSFT,GOOGL): ")
    symbols = [s.strip().upper() for s in symbols_input.split(',')]
    
    years = input("Enter number of years of data (default: 3): ")
    years = int(years) if years else 3
    
    quick_download(symbols, days=365*years)


# =============================================================================
# MAIN MENU
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   STOCK DATA DOWNLOADER                              ║
║                   (Yahoo Finance - FREE)                             ║
╚══════════════════════════════════════════════════════════════════════╝

This script will download historical stock data and save it in CSV format
compatible with your backtesting system.

Choose an option:
    """)
    
    print("1. Quick Download - Single Stock (AAPL, 3 years)")
    print("2. Download Tech Stocks (AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA)")
    print("3. Download Dow Stocks (10 major stocks)")
    print("4. Custom Download (Choose your own stocks)")
    print("5. Quick Test (AAPL, 1 year - for testing)")
    
    choice = input("\nEnter your choice (1-5) or press Enter for option 1: ").strip()
    
    if choice == '2':
        download_tech_stocks()
    elif choice == '3':
        download_dow_stocks()
    elif choice == '4':
        download_custom()
    elif choice == '5':
        print("\n🧪 TEST MODE: Downloading AAPL (1 year)")
        quick_download('AAPL', days=365)
    else:
        # Default option 1
        print("\n📥 QUICK DOWNLOAD: AAPL (3 years)")
        quick_download('AAPL', days=365*3)
    
    # Show preview of first file
    if os.path.exists('data/AAPL.csv'):
        print("\n" + "="*70)
        print("📋 Preview of AAPL.csv:")
        print("="*70)
        df = pd.read_csv('data/AAPL.csv')
        print(df.head(10))
        print(f"\n... ({len(df)} total rows)")
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                          NEXT STEPS                                  ║
╚══════════════════════════════════════════════════════════════════════╝

1. ✅ Your CSV files are in the 'data' folder
2. ✅ Files are formatted correctly for backtesting

3. Now run your backtest:

   python complete_backtest_system.py

   Or update the configuration in the script:
   
   csv_dir = '/Users/shreyanshsingh/mp_env/data'
   symbol_list = ['AAPL']  # Add the symbols you downloaded
    """)
