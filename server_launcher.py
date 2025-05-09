"""
MT9 EMA Backtester Server Launcher

This module provides a lightweight API endpoint that can be used to start
the main API server when it's not running. It acts as a "bootstrap" server
that can be contacted by the dashboard when the main server is down.

Usage:
    1. Run this script in the background (it uses minimal resources)
    2. When the main API server is down, the dashboard can contact this launcher
    3. The launcher will attempt to start the main API server

This provides a seamless user experience - when the user clicks the "offline"
status indicator, this launcher will attempt to bring the main server online.
"""

import os
import sys
import time
import logging
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psutil
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server_launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server_launcher")

# Constants
LAUNCHER_PORT = 5001  # Different from the main API port (5000)
API_SERVER_PORT = 5000
API_SERVER_HOST = "localhost"
API_CHECK_URL = f"http://{API_SERVER_HOST}:{API_SERVER_PORT}/api/status"
MAX_START_ATTEMPTS = 3
START_ATTEMPT_DELAY = 5  # seconds

# Global state
server_process: Optional[subprocess.Popen] = None
server_start_time: Optional[float] = None
last_status_check: Optional[float] = None
last_status: Dict[str, Any] = {"status": "unknown"}
server_start_attempts: int = 0

# Initialize FastAPI app
app = FastAPI(
    title="MT9 EMA Backtester Server Launcher",
    description="A lightweight service to start the main API server when needed",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            return True
    return False


def is_api_server_running() -> Tuple[bool, Dict[str, Any]]:
    """Check if the main API server is running and responsive."""
    global last_status_check, last_status
    
    # Use cached status if checked recently (within 5 seconds)
    current_time = time.time()
    if last_status_check and current_time - last_status_check < 5:
        return "status" in last_status and last_status["status"] != "error", last_status
    
    # Check if port is in use
    if not is_port_in_use(API_SERVER_PORT):
        last_status = {"status": "offline"}
        last_status_check = current_time
        return False, last_status
    
    # Try to contact the API server
    try:
        response = requests.get(API_CHECK_URL, timeout=2)
        if response.status_code == 200:
            last_status = response.json()
            last_status_check = current_time
            return True, last_status
        else:
            last_status = {"status": "error", "message": f"API returned status code {response.status_code}"}
            last_status_check = current_time
            return False, last_status
    except requests.RequestException as e:
        last_status = {"status": "error", "message": str(e)}
        last_status_check = current_time
        return False, last_status


def start_api_server() -> Dict[str, Any]:
    """Start the main API server as a subprocess."""
    global server_process, server_start_time, server_start_attempts
    
    # Check if we've hit the maximum number of attempts
    if server_start_attempts >= MAX_START_ATTEMPTS:
        logger.error(f"Maximum start attempts reached ({MAX_START_ATTEMPTS})")
        return {
            "success": False,
            "message": f"Failed to start server after {MAX_START_ATTEMPTS} attempts. Please check the logs."
        }
    
    # Check if server is already running
    running, status = is_api_server_running()
    if running:
        logger.info("API server is already running")
        return {"success": True, "message": "Server is already running", "status": status}
    
    # Check if server was started recently and might still be starting up
    if server_start_time and time.time() - server_start_time < 30:
        return {
            "success": False,
            "message": "Server start was attempted recently and may still be starting up"
        }
    
    try:
        # Get the path to the current Python executable and API server script
        python_exe = sys.executable
        api_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_server.py")
        
        # Check if the API server script exists
        if not os.path.exists(api_server_path):
            return {"success": False, "message": f"API server script not found: {api_server_path}"}
        
        # Start the API server as a separate process
        logger.info(f"Starting API server with: {python_exe} {api_server_path}")
        
        # Use a different approach depending on the OS
        if os.name == 'nt':  # Windows
            # On Windows, use CREATE_NEW_CONSOLE to create a visible window
            server_process = subprocess.Popen(
                [python_exe, api_server_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=os.path.dirname(api_server_path)
            )
        else:  # Unix-like
            # On Unix, just start the process normally
            server_process = subprocess.Popen(
                [python_exe, api_server_path],
                cwd=os.path.dirname(api_server_path)
            )
        
        server_start_time = time.time()
        server_start_attempts += 1
        
        # Give the server a moment to start up before returning
        time.sleep(2)
        
        # Schedule a status check to verify the server started successfully
        threading.Timer(5.0, check_server_status).start()
        
        return {
            "success": True,
            "message": "API server starting...",
            "pid": server_process.pid
        }
    except Exception as e:
        logger.error(f"Error starting API server: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Error starting server: {str(e)}"
        }


def check_server_status():
    """Check if the server started successfully."""
    global server_start_attempts
    
    running, _ = is_api_server_running()
    if running:
        logger.info("API server started successfully")
        server_start_attempts = 0  # Reset attempts counter on success
    else:
        logger.warning("API server did not start successfully")
        # If we've failed but still have attempts left, try again
        if server_start_attempts < MAX_START_ATTEMPTS:
            logger.info(f"Retrying server start (attempt {server_start_attempts + 1}/{MAX_START_ATTEMPTS})")
            time.sleep(START_ATTEMPT_DELAY)
            start_api_server()


@app.get("/launcher/status")
async def get_launcher_status():
    """Get the current status of the launcher and API server."""
    running, api_status = is_api_server_running()
    
    return {
        "launcher": {
            "status": "online",
            "version": "1.0.0",
            "port": LAUNCHER_PORT
        },
        "api_server": {
            "status": "online" if running else "offline",
            "last_checked": last_status_check,
            "details": api_status if running else {"message": "API server is not running"}
        },
        "start_info": {
            "last_attempt": server_start_time,
            "attempts": server_start_attempts,
            "max_attempts": MAX_START_ATTEMPTS
        }
    }


@app.post("/launcher/start")
async def launch_api_server():
    """Start the main API server if it's not already running."""
    result = start_api_server()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


if __name__ == "__main__":
    try:
        # Check if the launcher port is already in use
        if is_port_in_use(LAUNCHER_PORT):
            logger.error(f"Port {LAUNCHER_PORT} is already in use. Cannot start launcher.")
            sys.exit(1)
        
        # Check if the API server is already running
        running, _ = is_api_server_running()
        if not running:
            logger.info("API server is not running. It will be started when requested.")
        else:
            logger.info("API server is already running.")
        
        # Start the launcher
        logger.info(f"Starting launcher on port {LAUNCHER_PORT}")
        uvicorn.run(app, host="0.0.0.0", port=LAUNCHER_PORT)
    except Exception as e:
        logger.error(f"Error starting launcher: {str(e)}", exc_info=True)
        sys.exit(1)
