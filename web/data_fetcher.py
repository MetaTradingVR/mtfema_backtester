import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_fetcher')

def fetch_market_data(symbol, start_date, end_date, timeframe='1d'):
    """
    Fetch market data for the specified symbol and timeframe.
    
    Args:
        symbol (str): Trading symbol (e.g., 'ES', 'NQ', 'AAPL')
        start_date (datetime): Start date for data retrieval
        end_date (datetime): End date for data retrieval
        timeframe (str): Data timeframe ('1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo')
    
    Returns:
        pd.DataFrame: OHLCV data with datetime index
    """
    # Map our timeframe notation to yfinance notation
    timeframe_map = {
        '1m': '1m',
        '3m': '3m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '1d': '1d',
        '1w': '1wk',
        '1M': '1mo'
    }
    
    # Handle futures contracts by mapping to YF symbols
    futures_map = {
        'ES': 'ES=F',  # E-mini S&P 500
        'NQ': 'NQ=F',  # E-mini Nasdaq-100
        'YM': 'YM=F',  # E-mini Dow
        'RTY': 'RTY=F', # E-mini Russell 2000
        'CL': 'CL=F',  # Crude Oil
        'GC': 'GC=F',  # Gold
        'SI': 'SI=F',  # Silver
        'NG': 'NG=F',  # Natural Gas
        'ZC': 'ZC=F',  # Corn
        'ZS': 'ZS=F',  # Soybeans
        'ZW': 'ZW=F',  # Wheat
        'HG': 'HG=F',  # Copper
    }
    
    # Map forex pairs to YF symbols
    forex_map = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'USDJPY=X',
        'AUDUSD': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
        'EURGBP': 'EURGBP=X',
        'EURJPY': 'EURJPY=X',
    }
    
    # Map crypto to YF symbols
    crypto_map = {
        'BTCUSD': 'BTC-USD',
        'ETHUSD': 'ETH-USD',
        'LTCUSD': 'LTC-USD',
        'XRPUSD': 'XRP-USD',
        'ADAUSD': 'ADA-USD',
        'DOTUSD': 'DOT-USD',
        'SOLUSD': 'SOL-USD',
    }
    
    # Determine the appropriate symbol for yfinance
    if symbol in futures_map:
        yf_symbol = futures_map[symbol]
    elif symbol in forex_map:
        yf_symbol = forex_map[symbol]
    elif symbol in crypto_map:
        yf_symbol = crypto_map[symbol]
    else:
        # Assume it's a stock ticker
        yf_symbol = symbol
    
    # Convert timeframe to yfinance format
    yf_timeframe = timeframe_map.get(timeframe, '1d')
    
    try:
        logger.info(f"Fetching {symbol} ({yf_symbol}) data from {start_date} to {end_date} with timeframe {yf_timeframe}")
        
        # Adjust start date for higher resolution data due to yfinance limitations
        if yf_timeframe in ['1m', '2m', '5m', '15m', '30m'] and (end_date - start_date).days > 60:
            logger.warning(f"yfinance only provides {yf_timeframe} data for the last 60 days. Adjusting start date.")
            adjusted_start = max(start_date, end_date - timedelta(days=60))
            data = yf.download(yf_symbol, start=adjusted_start, end=end_date, interval=yf_timeframe)
        else:
            data = yf.download(yf_symbol, start=start_date, end=end_date, interval=yf_timeframe)
        
        if data.empty:
            logger.warning(f"No data returned for {symbol}. Generating sample data.")
            return generate_sample_data(start_date, end_date, timeframe)
        
        # Process the data
        data = data.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        logger.info("Generating sample data instead")
        return generate_sample_data(start_date, end_date, timeframe)


def generate_sample_data(start_date, end_date, timeframe='1d'):
    """
    Generate sample OHLCV data when real data can't be fetched.
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        timeframe (str): Timeframe for the data
    
    Returns:
        pd.DataFrame: Sample OHLCV data
    """
    # Define timeframe in minutes
    timeframe_minutes = {
        '1m': 1,
        '3m': 3,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '2h': 120,
        '4h': 240,
        '8h': 480,
        '1d': 1440,
        '1w': 10080,
        '1M': 43200
    }
    
    minutes = timeframe_minutes.get(timeframe, 1440)  # Default to 1d
    
    # Generate date range
    if timeframe in ['1d', '1w', '1M']:
        # For daily and above, use calendar days
        if timeframe == '1d':
            freq = 'D'
        elif timeframe == '1w':
            freq = 'W'
        else:
            freq = 'M'
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    else:
        # For intraday, use business hours
        business_days = pd.date_range(start=start_date, end=end_date, freq='B')
        dates = []
        for day in business_days:
            # Trading hours: 9:30 AM to 4:00 PM
            start_time = day.replace(hour=9, minute=30)
            end_time = day.replace(hour=16, minute=0)
            
            # Generate timestamps for the day
            day_times = pd.date_range(start=start_time, end=end_time, freq=f'{minutes}min')
            dates.extend(day_times)
    
    # Generate sample price data
    n = len(dates)
    close_prices = generate_random_walk(n, drift=0.0001, volatility=0.001, starting_price=4200)
    
    # Generate OHLC from close prices
    data = []
    for i, date in enumerate(dates):
        close = close_prices[i]
        
        # Generate realistic intraday volatility
        daily_volatility = close * 0.005  # 0.5% daily volatility
        
        high = close + abs(np.random.normal(0, daily_volatility))
        low = close - abs(np.random.normal(0, daily_volatility))
        open_price = low + random.random() * (high - low)
        
        # Ensure OHLC relationships are preserved
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate volume with some randomness
        base_volume = 1000000
        volume = int(np.random.normal(base_volume, base_volume * 0.3))
        if volume < 0:
            volume = base_volume
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


def generate_random_walk(n, drift=0.0001, volatility=0.001, starting_price=100):
    """
    Generate a random walk price series with drift.
    
    Args:
        n (int): Number of steps
        drift (float): Average drift per step
        volatility (float): Volatility per step
        starting_price (float): Starting price
    
    Returns:
        list: Generated price series
    """
    prices = [starting_price]
    
    # Add some market regime changes
    regime_changes = [int(n * 0.25), int(n * 0.5), int(n * 0.75)]
    regimes = [
        {'drift': 0.0005, 'volatility': 0.0008},  # Bull market
        {'drift': -0.0003, 'volatility': 0.0015},  # Bear market
        {'drift': 0.0001, 'volatility': 0.0005},   # Sideways market
        {'drift': 0.0002, 'volatility': 0.0012}    # Recovery market
    ]
    
    current_regime = 0
    
    for i in range(1, n):
        # Check for regime change
        if i in regime_changes:
            current_regime = (current_regime + 1) % len(regimes)
            drift = regimes[current_regime]['drift']
            volatility = regimes[current_regime]['volatility']
        
        # Generate return with regime-specific parameters
        daily_return = np.random.normal(drift, volatility)
        
        # Add some mean reversion
        if len(prices) >= 20:
            # Calculate 20-period moving average
            ma20 = sum(prices[-20:]) / 20
            # Mean reversion factor
            mean_reversion = (ma20 - prices[-1]) * 0.05
            daily_return += mean_reversion
        
        # Calculate new price
        price = prices[-1] * (1 + daily_return)
        
        # Add some gaps occasionally
        if random.random() < 0.05:  # 5% chance of a gap
            gap_size = random.choice([-1, 1]) * random.uniform(0.005, 0.02)
            price *= (1 + gap_size)
        
        prices.append(price)
    
    return prices


def calculate_ema(data, period=9):
    """
    Calculate the Exponential Moving Average.
    
    Args:
        data (pd.DataFrame): OHLCV data
        period (int): EMA period
    
    Returns:
        pd.Series: EMA values
    """
    return data['close'].ewm(span=period, adjust=False).mean()


def calculate_extensions(data, ema, atr=None):
    """
    Calculate extensions from the EMA.
    
    Args:
        data (pd.DataFrame): OHLCV data
        ema (pd.Series): EMA values
        atr (pd.Series, optional): ATR values for normalization
    
    Returns:
        pd.Series: Extension values (normalized by ATR if provided)
    """
    extensions = (data['close'] - ema)
    
    if atr is not None:
        extensions = extensions / atr
        
    return extensions


def calculate_atr(data, period=14):
    """
    Calculate Average True Range.
    
    Args:
        data (pd.DataFrame): OHLCV data
        period (int): ATR period
    
    Returns:
        pd.Series: ATR values
    """
    high = data['high']
    low = data['low']
    close = data['close'].shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)
    
    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr 