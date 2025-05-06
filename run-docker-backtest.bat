@echo off
echo Multi-Timeframe 9 EMA Extension Strategy Backtester (Docker)
echo ===========================================================
echo.

REM Default parameters
set SYMBOL=NQ
set TIMEFRAMES=1d,1h,15m
set START_DATE=2023-01-01
set END_DATE=2023-06-01
set INITIAL_CAPITAL=100000
set RISK_PER_TRADE=1.0
set MODE=backtest

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :execute
if /i "%~1"=="--symbol" (
    set SYMBOL=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--timeframes" (
    set TIMEFRAMES=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--start-date" (
    set START_DATE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--end-date" (
    set END_DATE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--capital" (
    set INITIAL_CAPITAL=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--risk" (
    set RISK_PER_TRADE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--mode" (
    set MODE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--help" (
    echo Usage: run-docker-backtest.bat [options]
    echo Options:
    echo   --symbol SYMBOL       Trading symbol (default: %SYMBOL%)
    echo   --timeframes TFS      Comma-separated timeframes (default: %TIMEFRAMES%)
    echo   --start-date DATE     Start date YYYY-MM-DD (default: %START_DATE%)
    echo   --end-date DATE       End date YYYY-MM-DD (default: %END_DATE%)
    echo   --capital AMOUNT      Initial capital (default: %INITIAL_CAPITAL%)
    echo   --risk PERCENT        Risk per trade %% (default: %RISK_PER_TRADE%)
    echo   --mode MODE           Mode: test, backtest, optimize (default: %MODE%)
    echo   --help                Show this help message
    exit /b 0
)
shift
goto :parse_args

:execute
echo Running in %MODE% mode
echo Symbol: %SYMBOL%
echo Timeframes: %TIMEFRAMES%
echo Period: %START_DATE% to %END_DATE%
echo Initial Capital: $%INITIAL_CAPITAL%
echo Risk Per Trade: %RISK_PER_TRADE%%%
echo.

REM Build the Docker image if needed
docker-compose build

REM Run the backtester in Docker
docker-compose run --rm mtfema-backtester --mode %MODE% --symbol %SYMBOL% --timeframes %TIMEFRAMES% --start-date %START_DATE% --end-date %END_DATE% --initial-capital %INITIAL_CAPITAL% --risk-per-trade %RISK_PER_TRADE% --save-plots

echo.
echo Backtester execution completed
echo Check the results directory for output files 