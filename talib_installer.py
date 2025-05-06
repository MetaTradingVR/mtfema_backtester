#!/usr/bin/env python
"""
TA-Lib Installer Script

This script automates the installation of TA-Lib, handling platform-specific
requirements and fallbacks to pandas-ta if installation fails.
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("talib_installer")

def get_python_version():
    """Get the current Python version as a string (e.g., '3.9')."""
    major, minor = sys.version_info.major, sys.version_info.minor
    return f"{major}.{minor}"

def get_platform_info():
    """Get platform information (OS, architecture)."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map architecture names
    if machine in ('amd64', 'x86_64'):
        arch = 'x64'
    elif machine in ('i386', 'i686', 'x86'):
        arch = 'x86'
    elif 'arm' in machine:
        arch = 'arm64' if '64' in machine else 'arm'
    else:
        arch = machine
        
    return system, arch

def install_talib():
    """Install TA-Lib package."""
    system, arch = get_platform_info()
    python_version = get_python_version()
    
    logger.info(f"Detected system: {system}, architecture: {arch}, Python: {python_version}")
    
    # Try to install TA-Lib using pip
    try:
        logger.info("Attempting to install TA-Lib via pip...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'TA-Lib'])
        logger.info("TA-Lib installed successfully via pip!")
        return True
    except subprocess.CalledProcessError:
        logger.warning("Standard pip installation failed. Trying alternative methods...")
    
    # For Windows, try to use wheels
    if system == 'windows':
        try:
            wheel_url = get_windows_wheel_url(python_version, arch)
            if wheel_url:
                logger.info(f"Installing TA-Lib from wheel: {wheel_url}")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', wheel_url])
                logger.info("TA-Lib installed successfully from wheel!")
                return True
        except Exception as e:
            logger.warning(f"Failed to install from wheel: {e}")
    
    # For Unix-like systems
    elif system in ('linux', 'darwin'):
        try:
            if install_unix_talib(system):
                return True
        except Exception as e:
            logger.warning(f"Failed to install on {system}: {e}")
    
    # Fallback to pandas-ta
    logger.warning("TA-Lib installation failed. Falling back to pandas-ta...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas-ta'])
        logger.info("pandas-ta installed successfully as a fallback!")
        
        # Create a wrapper module to redirect TA-Lib imports to pandas-ta
        create_talib_wrapper()
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install pandas-ta: {e}")
        return False

def get_windows_wheel_url(python_version, arch):
    """Get the appropriate wheel URL for the given Python version and architecture on Windows."""
    # Map of Python versions to wheel URLs
    wheels = {
        '3.7': f'https://download.lfd.uci.edu/pythonlibs/archived/TA_Lib-0.4.24-cp37-cp37m-win_{arch}.whl',
        '3.8': f'https://download.lfd.uci.edu/pythonlibs/archived/TA_Lib-0.4.24-cp38-cp38-win_{arch}.whl',
        '3.9': f'https://download.lfd.uci.edu/pythonlibs/archived/TA_Lib-0.4.24-cp39-cp39-win_{arch}.whl',
        '3.10': f'https://download.lfd.uci.edu/pythonlibs/archived/TA_Lib-0.4.24-cp310-cp310-win_{arch}.whl',
        '3.11': f'https://download.lfd.uci.edu/pythonlibs/archived/TA_Lib-0.4.24-cp311-cp311-win_{arch}.whl',
    }
    
    return wheels.get(python_version)

def install_unix_talib(system):
    """Install TA-Lib on Unix-like systems."""
    if system == 'linux':
        # Try apt (Debian/Ubuntu)
        try:
            logger.info("Attempting to install TA-Lib via apt...")
            subprocess.check_call(['sudo', 'apt-get', 'update'])
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'build-essential', 'ta-lib'])
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'TA-Lib'])
            logger.info("TA-Lib installed successfully via apt!")
            return True
        except subprocess.CalledProcessError:
            # Try yum (RHEL/CentOS/Fedora)
            try:
                logger.info("Attempting to install TA-Lib via yum...")
                subprocess.check_call(['sudo', 'yum', 'install', '-y', 'gcc', 'gcc-c++', 'make', 'ta-lib-devel'])
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'TA-Lib'])
                logger.info("TA-Lib installed successfully via yum!")
                return True
            except subprocess.CalledProcessError:
                logger.warning("Failed to install via package managers.")
                return False
    
    elif system == 'darwin':
        # macOS using Homebrew
        try:
            logger.info("Attempting to install TA-Lib via Homebrew...")
            subprocess.check_call(['brew', 'install', 'ta-lib'])
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'TA-Lib'])
            logger.info("TA-Lib installed successfully via Homebrew!")
            return True
        except subprocess.CalledProcessError:
            logger.warning("Failed to install via Homebrew.")
            return False
    
    return False

def create_talib_wrapper():
    """Create a wrapper module to redirect TA-Lib imports to pandas-ta."""
    wrapper_dir = Path("mtfema_backtester/utils/talib_wrapper")
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py with import redirects
    init_file = wrapper_dir / "__init__.py"
    with open(init_file, 'w') as f:
        f.write("""# TA-Lib wrapper using pandas-ta
import pandas as pd
import pandas_ta as ta
import numpy as np

# Map common TA-Lib functions to pandas-ta equivalents
def SMA(values, timeperiod=30):
    series = pd.Series(values)
    return series.ta.sma(length=timeperiod).values

def EMA(values, timeperiod=30):
    series = pd.Series(values)
    return series.ta.ema(length=timeperiod).values

def RSI(values, timeperiod=14):
    series = pd.Series(values)
    return series.ta.rsi(length=timeperiod).values

def BBANDS(values, timeperiod=5, nbdevup=2, nbdevdn=2):
    series = pd.Series(values)
    bbands = series.ta.bbands(length=timeperiod, std=nbdevup)
    upper = bbands[f'BBU_{timeperiod}_{nbdevup}'].values
    middle = bbands[f'BBM_{timeperiod}_{nbdevup}'].values
    lower = bbands[f'BBL_{timeperiod}_{nbdevup}'].values
    return upper, middle, lower

def MACD(values, fastperiod=12, slowperiod=26, signalperiod=9):
    series = pd.Series(values)
    macd = series.ta.macd(fast=fastperiod, slow=slowperiod, signal=signalperiod)
    macd_line = macd[f'MACD_{fastperiod}_{slowperiod}_{signalperiod}'].values
    signal_line = macd[f'MACDs_{fastperiod}_{slowperiod}_{signalperiod}'].values
    hist = macd[f'MACDh_{fastperiod}_{slowperiod}_{signalperiod}'].values
    return macd_line, signal_line, hist

# Add more functions as needed
""")
    
    logger.info(f"Created TA-Lib wrapper at {init_file}")
    logger.info("You can now import from mtfema_backtester.utils.talib_wrapper instead of talib")

if __name__ == "__main__":
    success = install_talib()
    if success:
        print("\n✅ TA-Lib installed successfully!")
    else:
        print("\n⚠️ TA-Lib installation failed, but pandas-ta fallback is available.")
        print("   To use the fallback, import from mtfema_backtester.utils.talib_wrapper instead of talib") 