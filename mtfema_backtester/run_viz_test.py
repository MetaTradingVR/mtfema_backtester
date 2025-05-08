#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Runner for visualization tests

This script is a simple runner to launch the visualization tests
for the MTFEMA backtester project.

Timestamp: 2025-05-06 PST
"""

import sys
import logging

if __name__ == "__main__":
    from mtfema_backtester.tools.viz_test import run_visualization_tests
    
    logging.basicConfig(level=logging.INFO)
    success = run_visualization_tests()
    sys.exit(0 if success else 1) 