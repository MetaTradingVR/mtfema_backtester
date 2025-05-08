#!/usr/bin/env python
"""
Multi-Timeframe 9 EMA Extension Strategy Backtester - Visualization Test
(Added 2025-05-06)

This script generates sample data and tests the visualization components.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the project directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import visualization components
from visualization.plotly_charts import (
    create_extension_map,
    create_signal_timeline,
    create_progression_tracker,
    create_conflict_map,
    create_conflict_type_chart,
    create_equity_curve,
    generate_sample_extension_data,
    generate_sample_signals_data,
    generate_sample_progression_data,
    generate_sample_conflict_data,
    save_figure
)

def run_visualization_tests():
    """Generate sample data and test all visualization components."""
    # Set up sample data parameters
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create output directory
    output_dir = os.path.join(script_dir, "output", "viz_test")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Running visualization tests. Output will be saved to: {output_dir}")
    
    # Test 1: Extension Map
    print("Testing Extension Map...")
    extension_data = generate_sample_extension_data(timeframes, dates)
    extension_map = create_extension_map(extension_data, "MT 9 EMA Extension Map")
    save_path = save_figure(extension_map, "extension_map", output_dir)
    print(f"Saved to: {save_path}")
    
    # Test 2: Signal Timeline
    print("Testing Signal Timeline...")
    signals_data = generate_sample_signals_data(timeframes, dates, num_signals=100)
    signal_timeline = create_signal_timeline(signals_data, "MT 9 EMA Signal Timeline")
    save_path = save_figure(signal_timeline, "signal_timeline", output_dir)
    print(f"Saved to: {save_path}")
    
    # Test 3: Progression Tracker
    print("Testing Progression Tracker...")
    progression_data = generate_sample_progression_data(timeframes)
    progression_tracker = create_progression_tracker(progression_data, "MT 9 EMA Progression Tracker")
    save_path = save_figure(progression_tracker, "progression_tracker", output_dir)
    print(f"Saved to: {save_path}")
    
    # Test 4: Conflict Map
    print("Testing Conflict Map...")
    conflict_matrix, conflict_types, conflict_counts = generate_sample_conflict_data(timeframes)
    conflict_map = create_conflict_map(conflict_matrix, timeframes, "MT 9 EMA Conflict Map")
    save_path = save_figure(conflict_map, "conflict_map", output_dir)
    print(f"Saved to: {save_path}")
    
    # Test 5: Conflict Type Chart
    print("Testing Conflict Type Chart...")
    conflict_type_chart = create_conflict_type_chart(conflict_types, conflict_counts, "MT 9 EMA Conflict Types")
    save_path = save_figure(conflict_type_chart, "conflict_type_chart", output_dir)
    print(f"Saved to: {save_path}")
    
    # Test 6: Equity Curve
    print("Testing Equity Curve...")
    equity_values = np.cumprod(1 + np.random.normal(0.001, 0.015, size=len(dates))) * 100000
    equity_curve = create_equity_curve(dates, equity_values, "MT 9 EMA Equity Curve")
    save_path = save_figure(equity_curve, "equity_curve", output_dir)
    print(f"Saved to: {save_path}")
    
    print("\nAll visualization tests completed successfully!")
    print(f"HTML files saved to: {output_dir}")
    print("\nYou can open these files in your web browser to view the interactive visualizations.")

if __name__ == "__main__":
    run_visualization_tests() 