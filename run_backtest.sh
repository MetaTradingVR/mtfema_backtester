#!/bin/bash

echo "======================================="
echo "MT 9 EMA Backtester - Unix Launcher"
echo "======================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    source .venv/bin/activate
    python3 talib_installer.py
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Default parameters
SYMBOL="ES"
START_DATE="2023-01-01"
END_DATE="2023-12-31"
CAPITAL="100000"
RISK="0.01"
EXTRA_PARAMS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --start)
            START_DATE="$2"
            shift 2
            ;;
        --end)
            END_DATE="$2"
            shift 2
            ;;
        --capital)
            CAPITAL="$2"
            shift 2
            ;;
        --risk)
            RISK="$2"
            shift 2
            ;;
        *)
            EXTRA_PARAMS="$EXTRA_PARAMS $1"
            shift
            ;;
    esac
done

echo "Running MT 9 EMA Backtester..."
echo "Symbol: $SYMBOL"
echo "Date Range: $START_DATE to $END_DATE"
echo "Initial Capital: $$CAPITAL"
echo "Risk per Trade: $RISK"

python3 main.py --symbol "$SYMBOL" --start "$START_DATE" --end "$END_DATE" --capital "$CAPITAL" --risk "$RISK" $EXTRA_PARAMS

# Deactivate virtual environment
deactivate

echo ""
echo "Backtest complete!" 