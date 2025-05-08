#!/bin/bash
# Script to commit the MT 9 EMA Backtester Dashboard implementation

# Set terminal colors for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Staging dashboard implementation files...${NC}"

# Stage updated documentation
git add project_status.md
git add README.md

# Stage the entire dashboard directory
git add mtfema-dashboard/

# Stage other related files if any
git add run_web_app.py

# Commit the changes with a detailed message
echo -e "${BLUE}Committing dashboard implementation...${NC}"

git commit -m "Add Next.js dashboard for MT 9 EMA Backtester

This commit implements a comprehensive web dashboard using Next.js, Tailwind CSS, and Plotly.js:

- Created intuitive tabbed interface for different visualization views
- Implemented Parameter Heatmap for optimization analysis
- Added Parameter Impact Analysis for individual parameter evaluation
- Created Parallel Coordinates for multi-parameter relationship visualization
- Built Live Trading Dashboard for real-time performance monitoring
- Updated documentation to reflect new dashboard features
- Added installation and usage instructions"

echo -e "${GREEN}Dashboard implementation committed successfully!${NC}"
echo -e "${BLUE}Use 'git push' to upload changes to GitHub${NC}" 