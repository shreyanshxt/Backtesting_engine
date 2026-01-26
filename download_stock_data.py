#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stock Data Downloader
Downloads historical stock data from Yahoo Finance and saves as CSV files
Format compatible with HistoricCSVDataHandler
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta


def download_stock_data(symbol, start_date, end_date, output_dir='data'):
    """
    Download historical stock data from Yahoo Finance.
    
    Parameters:
    -----------
    symbol : str
        Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    start_date : str or datetime
        Start date for historical data (e.g., '2020-01-01')
    end_date : str or datetime
        End date for historical data (e.g., '2023-12-31')
    output_dir : str
        Directory to save CSV files (default: 'data')
    
    Returns:
    --------
    str : Path to the saved CSV file
    """
    print(f"\n📥 Downloading {symbol} data from {start_date} to {end_date}...")
    
    try:
        # Download data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"❌ No data found for {symbol}")
            return None
        
        # Rename columns to match our format
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Select only the columns we need
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Reset index to make datetime a column
        df.reset_index(inplace=True)
        df = df.rename(columns={'Date': 'datetime'})
        
        # Format datetime
        df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        output_file = os.path.join(output_dir, f'{symbol}.csv')
        df.to_csv(output_file, index=False)
        
        print(f"✅ Downloaded {len(df)} rows of data")
        print(f"📁 Saved to: {output_file}")
        print(f"📊 Date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error downloading {symbol}: {str(e)}")
        return None


def download_multiple_stocks(symbols, start_date, end_date, output_dir='data'):
    """
    Download data for multiple stocks.
    
    Parameters:
    -----------
    symbols : list
        List of stock ticker symbols
    start_date : str or datetime
        Start date for historical data
    end_date : str or datetime
        End date for historical data
    output_dir : str
        Directory to save CSV files
    
    Returns:
    --------
    dict : Dictionary mapping symbols to their CSV file paths
    """
    print("="*60)
    print("STOCK DATA DOWNLOADER")
    print("="*60)
    
    results = {}
    
    for symbol in symbols:
        file_path = download_stock_data(symbol, start_date, end_date, output_dir)
        if file_path:
            results[symbol] = file_path
    
    print("\n" + "="*60)
    print(f"📊 DOWNLOAD COMPLETE: {len(results)}/{len(symbols)} successful")
    print("="*60)
    
    if results:
        print("\n✅ Successfully downloaded:")
        for symbol, path in results.items():
            print(f"   • {symbol}: {path}")
    
    failed = set(symbols) - set(results.keys())
    if failed:
        print("\n❌ Failed downloads:")
        for symbol in failed:
            print(f"   • {symbol}")
    
    return results


def preview_csv(csv_file, n_rows=10):
    """
    Preview the downloaded CSV file.
    
    Parameters:
    -----------
    csv_file : str
        Path to CSV file
    n_rows : int
        Number of rows to display (default: 10)
    """
    print(f"\n📋 Preview of {csv_file}:")
    print("-" * 80)
    
    df = pd.read_csv(csv_file)
    print(df.head(n_rows))
    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns.tolist())}")
    print("-" * 80)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           STOCK DATA DOWNLOADER (Yahoo Finance)              ║
    ║                                                              ║
    ║  This script downloads historical stock data and saves      ║
    ║  it in CSV format compatible with your backtesting system.  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    symbols = [
    'RELIANCE.NS',
    'TCS.NS',
    'INFY.NS',
    'HDFCBANK.NS',
    'ICICIBANK.NS'
    ]

    start_date = '2020-01-01'
    end_date   = '2023-12-31'
    output_dir = 'data'
       # Output directory
    
    # Option 1: Download multiple stocks
    results = download_multiple_stocks(symbols, start_date, end_date, output_dir)
    
    # Option 2: Download a single stock
    # download_stock_data('AAPL', '2020-01-01', '2023-12-31', 'data')
    
    # Preview the first file
    if results:
        first_file = list(results.values())[0]
        preview_csv(first_file)
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                      NEXT STEPS                              ║
    ║                                                              ║
    ║  1. Check the 'data' folder for your CSV files              ║
    ║  2. Update your backtest configuration:                     ║
    ║     csv_dir = '/Users/shreyanshsingh/mp_env/data'           ║
    ║     symbol_list = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']        ║
    ║  3. Run your backtest using complete_backtest_system.py     ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
