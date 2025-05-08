#!/usr/bin/env python
"""
Multi-Timeframe 9 EMA Extension Strategy Backtester - Web Interface
(Added 2025-05-06)

This script launches the Streamlit-based web interface for the MT 9 EMA Backtester.
"""

import os
import sys
import subprocess

def main():
    """Launch the Streamlit web application."""
    # Get the current script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Streamlit app
    app_path = os.path.join(script_dir, "web", "app.py")
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        print(f"Error: Could not find app file at {app_path}")
        sys.exit(1)
    
    # Launch Streamlit
    try:
        print("Launching MT 9 EMA Backtester Web Interface...")
        
        # Build the command
        cmd = ["streamlit", "run", app_path, "--server.port=8501"]
        
        # Check for any command-line arguments
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        # Run Streamlit
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down web interface...")
    except Exception as e:
        print(f"Error launching web interface: {str(e)}")
        
        # Check if Streamlit is installed
        try:
            import streamlit
            print(f"Streamlit is installed (version {streamlit.__version__})")
        except ImportError:
            print("Streamlit is not installed. Please install it using:")
            print("pip install streamlit")
            print("\nThen run this script again.")

if __name__ == "__main__":
    main() 