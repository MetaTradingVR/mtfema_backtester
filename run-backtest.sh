#!/bin/bash

echo "Multi-Timeframe 9 EMA Extension Strategy Backtester"
echo "==================================================="

# Activate the virtual environment if it exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Warning: Virtual environment not found. Please create it first using:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r mtfema_backtester/requirements.txt"
fi

# Set default parameters
SYMBOL="SPY"
TIMEFRAMES="1d,1h,15m"
START_DATE="2022-01-01"
END_DATE="2023-01-01"
INITIAL_CAPITAL="100000"
RISK_PER_TRADE="1.0"
MODE="backtest"

# Parse command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --symbol)
            SYMBOL="$2"
            shift 2
            ;;
        --timeframes)
            TIMEFRAMES="$2"
            shift 2
            ;;
        --start-date)
            START_DATE="$2"
            shift 2
            ;;
        --end-date)
            END_DATE="$2"
            shift 2
            ;;
        --capital)
            INITIAL_CAPITAL="$2"
            shift 2
            ;;
        --risk)
            RISK_PER_TRADE="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./run-backtest.sh [options]"
            echo "Options:"
            echo "  --symbol SYMBOL       Trading symbol (default: $SYMBOL)"
            echo "  --timeframes TFS      Comma-separated timeframes (default: $TIMEFRAMES)"
            echo "  --start-date DATE     Start date YYYY-MM-DD (default: $START_DATE)"
            echo "  --end-date DATE       End date YYYY-MM-DD (default: $END_DATE)"
            echo "  --capital AMOUNT      Initial capital (default: $INITIAL_CAPITAL)"
            echo "  --risk PERCENT        Risk per trade % (default: $RISK_PER_TRADE)"
            echo "  --mode MODE           Mode: test, backtest, optimize (default: $MODE)"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

echo "Running in $MODE mode"
echo "Symbol: $SYMBOL"
echo "Timeframes: $TIMEFRAMES"
echo "Period: $START_DATE to $END_DATE"
echo "Initial Capital: \$$INITIAL_CAPITAL"
echo "Risk Per Trade: $RISK_PER_TRADE%"
echo ""

# Execute the backtester
python -m mtfema_backtester.main --mode $MODE --symbol $SYMBOL --timeframes $TIMEFRAMES --start-date $START_DATE --end-date $END_DATE --initial-capital $INITIAL_CAPITAL --risk-per-trade $RISK_PER_TRADE --save-plots

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Backtester execution failed with code $?"
    exit $?
fi

echo ""
echo "Backtest completed successfully"
echo "Results saved to ./output/$MODE/"

# Make the script executable
chmod +x run-backtest.sh 