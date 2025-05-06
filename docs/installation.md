# Installation Guide

This guide will help you install and set up the Multi-Timeframe 9 EMA Extension Strategy Backtester.

## System Requirements

- **Python**: Version 3.7+ (3.13 recommended)
- **OS**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB+ recommended for large datasets)
- **Disk Space**: ~100MB for the application, plus additional space for data and results

## Option 1: Standard Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/mtfema-backtester.git
cd mtfema-backtester
```

### Step 2: Create a Virtual Environment

#### Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

#### macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r mtfema_backtester/requirements.txt
```

### Step 4: Install TA-Lib (Optional but Recommended)

The backtester can use either TA-Lib or pandas-ta for technical indicators. TA-Lib is significantly faster but requires a separate installation.

#### Automatic Installation (Windows):
```bash
python -m mtfema_backtester.utils.talib_installer
```

#### Manual Installation:

##### Windows:
```powershell
# Replace cp310 with your Python version (e.g., cp39, cp310, cp311)
pip install --no-cache-dir -U https://github.com/mrjbq7/ta-lib/releases/download/0.4.24/TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
```

##### macOS:
```bash
brew install ta-lib
pip install ta-lib
```

##### Linux:
```bash
# Install dependencies
sudo apt-get install build-essential
sudo apt-get install python3-dev

# Download and install TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install ta-lib
```

### Step 5: Install Performance Enhancements (Optional)

For better performance, especially with large datasets:

```bash
pip install numba
```

## Option 2: Docker Installation

For an isolated environment that works across all platforms:

### Step 1: Install Docker

Follow the [official Docker installation guide](https://docs.docker.com/get-docker/) for your platform.

### Step 2: Run the Docker Image

```bash
docker pull yourusername/mtfema-backtester:latest
docker run -it -v $(pwd)/data:/app/data -v $(pwd)/results:/app/results yourusername/mtfema-backtester:latest
```

This will mount your local `data` and `results` directories to the container.

## Verifying Installation

To verify that the installation was successful, run:

```bash
python -m mtfema_backtester.main --mode test
```

You should see output indicating that the test was successful and some sample results.

## Configuration

After installation, you may want to create a custom configuration file:

```bash
# Copy the default configuration
cp mtfema_backtester/config.yaml ./my_config.yaml
```

Edit `my_config.yaml` with your preferred settings, then use it with:

```bash
python -m mtfema_backtester.main --config my_config.yaml
```

## Troubleshooting

### TA-Lib Installation Issues

If you encounter problems installing TA-Lib:

1. Ensure you have a C/C++ compiler installed (Visual Studio on Windows, XCode on macOS)
2. Try installing a pre-compiled wheel for your platform
3. Fall back to pandas-ta (slower but more compatible)

### Common Errors

#### ModuleNotFoundError

Make sure you are running the commands from the project root directory and your virtual environment is activated.

#### ImportError with TA-Lib

This is often due to missing system dependencies. See the manual installation instructions above for your platform.

#### Memory Errors with Large Datasets

Try reducing the amount of data or timeframes you're processing, or increase the available memory.

## Next Steps

After installation, head over to the [Quick Start Guide](quickstart.md) to run your first backtest. 