"""
TA-Lib Installation Helper for Windows Systems
This utility automatically detects Python version and system architecture,
and installs the appropriate TA-Lib wheel package.
"""

import os
import sys
import platform
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for TA-Lib wheels
TALIB_WHEEL_BASE_URL = "https://github.com/mrjbq7/ta-lib/releases/download/0.4.24"

def get_python_version():
    """Get the Python version and architecture"""
    py_version = f"{sys.version_info.major}{sys.version_info.minor}"
    py_arch = "win_amd64" if platform.architecture()[0] == "64bit" else "win32"
    return py_version, py_arch

def install_talib_from_wheel():
    """Install TA-Lib from pre-compiled wheel for the current Python version"""
    py_version, py_arch = get_python_version()
    wheel_name = f"TA_Lib-0.4.24-cp{py_version}-cp{py_version}-{py_arch}.whl"
    wheel_url = f"{TALIB_WHEEL_BASE_URL}/{wheel_name}"
    
    logger.info(f"Detected Python {py_version} ({py_arch})")
    logger.info(f"Attempting to install TA-Lib from wheel: {wheel_name}")
    
    # Try to install the wheel
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--no-cache-dir", "-U", wheel_url
        ])
        logger.info("TA-Lib installation successful!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing TA-Lib wheel: {str(e)}")
        return False

def install_pandas_ta_alternative():
    """Install pandas-ta as an alternative to TA-Lib"""
    logger.info("Installing pandas-ta as an alternative to TA-Lib")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pandas-ta"
        ])
        logger.info("pandas-ta installation successful!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing pandas-ta: {str(e)}")
        return False

def check_talib_installation():
    """Check if TA-Lib is already installed"""
    try:
        import talib
        logger.info(f"TA-Lib is already installed (version: {talib.__version__})")
        return True
    except ImportError:
        logger.info("TA-Lib is not installed")
        return False

def setup_talib():
    """Main function to set up TA-Lib"""
    if check_talib_installation():
        return True
    
    if platform.system() == "Windows":
        success = install_talib_from_wheel()
        if success:
            return True
    
    # If we get here, either we're not on Windows or the wheel installation failed
    logger.warning("Falling back to pandas-ta as an alternative to TA-Lib")
    return install_pandas_ta_alternative()

if __name__ == "__main__":
    if setup_talib():
        logger.info("TA-Lib or alternative successfully installed")
        sys.exit(0)
    else:
        logger.error("Failed to install TA-Lib or alternative")
        sys.exit(1) 