#!/bin/bash

echo "Multi-Timeframe 9 EMA Extension Strategy Backtester (Docker)"
echo "==========================================================="
echo

# Default parameters
SYMBOL="NQ"
TIMEFRAMES="1d,1h,15m"
START_DATE="2023-01-01"
END_DATE="2023-06-01"
INITIAL_CAPITAL="100000"
RISK_PER_TRADE="1.0"
MODE="backtest"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
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
      echo "Usage: ./run-docker-backtest.sh [options]"
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
echo

# Make the script executable if necessary
chmod +x "$0"

# Build the Docker image if needed
docker-compose build

# Run the backtester in Docker
docker-compose run --rm mtfema-backtester \
  --mode "$MODE" \
  --symbol "$SYMBOL" \
  --timeframes "$TIMEFRAMES" \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --initial-capital "$INITIAL_CAPITAL" \
  --risk-per-trade "$RISK_PER_TRADE" \
  --save-plots

echo
echo "Backtester execution completed"
echo "Check the results directory for output files" 