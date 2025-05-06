@echo off
echo Running Multi-Timeframe 9 EMA Extension Strategy Test...
echo.
echo This will:
echo  1. Load test data and calculate indicators
echo  2. Test the extension detector
echo  3. Generate visualizations and HTML report
echo.
echo The HTML report will open automatically in your browser when complete.
echo.

:: Try to find the Python executable
where py >nul 2>&1
if %ERRORLEVEL% == 0 (
    py -m mtfema_backtester.test_strategy
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% == 0 (
        python -m mtfema_backtester.test_strategy
    ) else (
        echo Python executable not found. Please install Python or add it to PATH.
        exit /b 1
    )
)

echo.
echo Test completed.
echo.
echo Results are available in the 'results' directory.
echo.
pause 