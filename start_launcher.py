"""
Start the server launcher in the background.
This script starts the server_launcher.py file which is used to start the main API server when needed.
"""

import os
import sys
import subprocess
import time
import psutil

def is_launcher_running():
    """Check if the server launcher is already running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a Python process running server_launcher.py
            cmdline = proc.info.get('cmdline')
            if cmdline and len(cmdline) > 1:
                if 'python' in cmdline[0].lower() and any('server_launcher.py' in cmd for cmd in cmdline):
                    print(f"Server launcher is already running (PID: {proc.info['pid']})") 
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, TypeError):
            # Added TypeError to catch any type issues with cmdline processing
            pass
    return False

def start_launcher():
    """Start the server launcher if it's not already running."""
    if is_launcher_running():
        return True

    print("Starting server launcher...")
    try:
        # Get the absolute path to server_launcher.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        launcher_path = os.path.join(script_dir, "server_launcher.py")
        
        # Use Popen with shell=False for better security
        process = subprocess.Popen(
            [sys.executable, launcher_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,  # Hide the console window
            cwd=script_dir
        )
        
        # Wait briefly to see if the process starts
        time.sleep(2)
        if process.poll() is None:  # None means process is still running
            print(f"Server launcher started successfully (PID: {process.pid})")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"Server launcher failed to start. Exit code: {process.returncode}")
            print(f"STDOUT: {stdout.decode('utf-8')}")
            print(f"STDERR: {stderr.decode('utf-8')}")
            return False
    except Exception as e:
        print(f"Error starting server launcher: {str(e)}")
        return False

if __name__ == "__main__":
    success = start_launcher()
    print(f"Launcher {'started successfully' if success else 'failed to start'}")
    sys.exit(0 if success else 1)
