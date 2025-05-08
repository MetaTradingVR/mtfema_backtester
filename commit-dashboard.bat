@echo off
REM Script to commit the MT 9 EMA Backtester Dashboard implementation

echo Staging dashboard implementation files...

REM Stage updated documentation
git add project_status.md
git add README.md

REM Stage the entire dashboard directory
git add mtfema-dashboard/

REM Stage other related files if any
git add run_web_app.py

REM Commit the changes with a detailed message
echo Committing dashboard implementation...

git commit -m "Add Next.js dashboard for MT 9 EMA Backtester

This commit implements a comprehensive web dashboard using Next.js, Tailwind CSS, and Plotly.js:

- Created intuitive tabbed interface for different visualization views
- Implemented Parameter Heatmap for optimization analysis
- Added Parameter Impact Analysis for individual parameter evaluation
- Created Parallel Coordinates for multi-parameter relationship visualization
- Built Live Trading Dashboard for real-time performance monitoring
- Updated documentation to reflect new dashboard features
- Added installation and usage instructions"

echo Dashboard implementation committed successfully!
echo Use 'git push' to upload changes to GitHub 