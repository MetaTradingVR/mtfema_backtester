"""
Web interface for the MTFEMA backtester

This package provides a Streamlit-based web interface for running backtests,
viewing visualization outputs, and adjusting strategy parameters interactively.

Timestamp: 2025-05-06 PST
"""

from mtfema_backtester.web.app import run_app

__all__ = ['run_app'] 