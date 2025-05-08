#!/bin/bash
# MT 9 EMA Backtester Dashboard Commit Script for Unix/Linux
# This script commits all dashboard changes to the repository

echo "MT 9 EMA Backtester Dashboard Commit Script"
echo "============================================="

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and try again."
    exit 1
fi

# Stage dashboard files
echo "Staging dashboard files..."
git add mtfema-dashboard
git add api_server.py
git add dashboard_guide.md
git add commit-dashboard.bat
git add commit-dashboard.sh

# Stage additional documentation files
echo "Staging documentation files..."
git add README.md
git add project_status.md

# Ask for commit message
echo ""
read -p "Enter commit message: " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Updated MT 9 EMA Backtester Dashboard"
fi

# Commit changes
echo ""
echo "Committing with message: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# Ask if user wants to push changes
echo ""
read -p "Push changes to remote repository? (y/n): " PUSH_CHANGES

if [[ $PUSH_CHANGES == "y" || $PUSH_CHANGES == "Y" ]]; then
    echo ""
    echo "Pushing changes to remote repository..."
    git push
    echo ""
    echo "Changes pushed successfully!"
else
    echo ""
    echo "Changes committed locally. Use 'git push' to push them to the remote repository when ready."
fi

echo ""
echo "Done!" 