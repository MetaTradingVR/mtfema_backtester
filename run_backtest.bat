@echo off
echo =======================================
echo MT 9 EMA Backtester - Windows Launcher
echo =======================================

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if it doesn't
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    call .venv\Scripts\activate.bat
    python talib_installer.py
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: Parse command line arguments
set params=
set symbol=ES
set start_date=2023-01-01
set end_date=2023-12-31
set capital=100000
set risk=0.01

:parse
if "%~1"=="" goto :execute
if /i "%~1"=="--symbol" (
    set symbol=%~2
    shift
    shift
    goto :parse
)
if /i "%~1"=="--start" (
    set start_date=%~2
    shift
    shift
    goto :parse
)
if /i "%~1"=="--end" (
    set end_date=%~2
    shift
    shift
    goto :parse
)
if /i "%~1"=="--capital" (
    set capital=%~2
    shift
    shift
    goto :parse
)
if /i "%~1"=="--risk" (
    set risk=%~2
    shift
    shift
    goto :parse
)

set params=%params% %1
shift
goto :parse

:execute
echo Running MT 9 EMA Backtester...
echo Symbol: %symbol%
echo Date Range: %start_date% to %end_date%
echo Initial Capital: $%capital%
echo Risk per Trade: %risk%

python main.py --symbol %symbol% --start %start_date% --end %end_date% --capital %capital% --risk %risk% %params%

:: Deactivate virtual environment
call .venv\Scripts\deactivate.bat

echo.
echo Backtest complete!
pause 