@echo off
REM MT 9 EMA Backtester Dashboard Commit Script for Windows
REM This script commits all dashboard changes to the repository

echo MT 9 EMA Backtester Dashboard Commit Script
echo =============================================

REM Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo Git is not installed or not in your PATH. Please install Git and try again.
  exit /b 1
)

REM Stage dashboard files
echo Staging dashboard files...
git add mtfema-dashboard
git add api_server.py
git add dashboard_guide.md
git add commit-dashboard.bat
git add commit-dashboard.sh

REM Stage additional documentation files
echo Staging documentation files...
git add README.md
git add project_status.md

REM Ask for commit message
set /p COMMIT_MSG="Enter commit message: "

if "%COMMIT_MSG%"=="" (
  set COMMIT_MSG="Updated MT 9 EMA Backtester Dashboard"
)

REM Commit changes
echo.
echo Committing with message: %COMMIT_MSG%
git commit -m %COMMIT_MSG%

REM Ask if user wants to push changes
set /p PUSH_CHANGES="Push changes to remote repository? (y/n): "

if /i "%PUSH_CHANGES%"=="y" (
  echo.
  echo Pushing changes to remote repository...
  git push
  echo.
  echo Changes pushed successfully!
) else (
  echo.
  echo Changes committed locally. Use 'git push' to push them to the remote repository when ready.
)

echo.
echo Done! 