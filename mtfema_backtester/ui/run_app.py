#!/usr/bin/env python
"""
Runner script for the Streamlit web UI
"""

import os
import sys
import subprocess
import argparse

def main():
    """
    Run the Streamlit app with appropriate arguments
    """
    parser = argparse.ArgumentParser(description="Run the MT 9 EMA Backtester Streamlit UI")
    parser.add_argument("--port", type=int, default=8501, help="Port to run the Streamlit app on")
    parser.add_argument("--browser", action="store_true", help="Automatically open browser")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args()
    
    # Determine the app.py path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    # Build command
    cmd = [
        "streamlit", "run", app_path,
        "--server.port", str(args.port)
    ]
    
    # Add browser option
    if not args.browser:
        cmd.extend(["--server.headless", "true"])
    
    # Run the Streamlit app
    print(f"Starting MT 9 EMA Backtester UI on port {args.port}...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
