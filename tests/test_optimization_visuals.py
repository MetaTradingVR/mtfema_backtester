"""
Test script for optimization visualizations.

This script tests the optimization visualization components in isolation
with generated sample data.
"""

import os
import sys
import pandas as pd
import numpy as np
import random
import webbrowser
from pathlib import Path

# Add the project root to the Python path to make imports work
sys.path.append(str(Path(__file__).parent.parent))

# Import visualization components
from mtfema_backtester.visualization.optimization_visuals import (
    create_optimization_heatmap,
    create_parameter_impact_chart,
    create_parallel_coordinates_plot,
    create_optimization_dashboard
)

def generate_sample_optimization_results(n_params=3, n_results=100):
    """Generate sample optimization results for testing."""
    print(f"Generating {n_results} sample optimization results...")
    
    # Define parameters for optimization
    params = [
        'ema_period',
        'extension_threshold',
        'reclamation_threshold',
        'risk_percent',
        'target_multiple'
    ]
    
    # Create random parameter combinations
    results = []
    for i in range(n_results):
        result = {
            'ema_period': np.random.choice([8, 9, 10, 11, 12]),
            'extension_threshold': round(random.uniform(1.0, 2.0), 1),
            'reclamation_threshold': round(random.uniform(0.3, 0.7), 1),
            'risk_percent': round(random.uniform(0.5, 2.0), 1),
            'target_multiple': round(random.uniform(1.5, 3.0), 1)
        }
        
        # Calculate performance metrics based on parameters
        # Here we simulate some correlation between params and metrics
        base_return = random.uniform(10, 40)
        param_effect = (
            (result['ema_period'] - 9) * -5 +
            (result['extension_threshold'] - 1.5) * -10 +
            (result['reclamation_threshold'] - 0.5) * 15 +
            (result['risk_percent'] - 1.0) * 8 +
            (result['target_multiple'] - 2.0) * 12
        )
        
        # Add some random noise
        noise = random.uniform(-10, 10)
        
        # Calculate metrics
        total_return = base_return + param_effect + noise
        win_rate = min(80, max(30, 50 + total_return/10 + random.uniform(-5, 5)))
        profit_factor = 1.0 + total_return/50
        max_drawdown = min(50, max(5, 30 - total_return/5 + random.uniform(-5, 5)))
        sharpe_ratio = total_return / (max_drawdown/2)
        sortino_ratio = sharpe_ratio * random.uniform(1.1, 1.5)
        calmar_ratio = total_return / max_drawdown
        avg_trade = total_return / random.randint(20, 40)
        
        # Add metrics to results
        result.update({
            'total_return': round(total_return, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'avg_trade': round(avg_trade, 2)
        })
        
        results.append(result)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    return df

def test_parameter_heatmap():
    """Test the parameter heatmap visualization."""
    print("\n=== Testing Parameter Heatmap ===")
    
    # Generate sample data
    results_df = generate_sample_optimization_results(n_results=50)
    
    # Create the heatmap
    fig = create_optimization_heatmap(
        results_df,
        param_x='ema_period',
        param_y='extension_threshold',
        metric='total_return',
        title="Test Heatmap: EMA Period vs Extension Threshold"
    )
    
    # Save to HTML file
    output_path = Path("test_outputs/parameter_heatmap.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    
    print(f"Parameter heatmap saved to {output_path}")
    print(f"Opening {output_path} in browser...")
    webbrowser.open(str(output_path))

def test_parameter_impact_chart():
    """Test the parameter impact chart visualization."""
    print("\n=== Testing Parameter Impact Chart ===")
    
    # Generate sample data
    results_df = generate_sample_optimization_results(n_params=5, n_results=100)
    
    # Create the impact chart
    fig = create_parameter_impact_chart(
        results_df,
        metric='total_return',
        n_params=5,
        title="Test Parameter Impact: Total Return"
    )
    
    # Save to HTML file
    output_path = Path("test_outputs/parameter_impact.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    
    print(f"Parameter impact chart saved to {output_path}")
    print(f"Opening {output_path} in browser...")
    webbrowser.open(str(output_path))

def test_parallel_coordinates_plot():
    """Test the parallel coordinates plot visualization."""
    print("\n=== Testing Parallel Coordinates Plot ===")
    
    # Generate sample data
    results_df = generate_sample_optimization_results(n_params=5, n_results=100)
    
    # Create the parallel coordinates plot
    fig = create_parallel_coordinates_plot(
        results_df,
        metric='total_return',
        top_n=30,
        title="Test Parallel Coordinates: Top 30 Parameter Combinations"
    )
    
    # Save to HTML file
    output_path = Path("test_outputs/parallel_coordinates.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    
    print(f"Parallel coordinates plot saved to {output_path}")
    print(f"Opening {output_path} in browser...")
    webbrowser.open(str(output_path))

def test_optimization_dashboard():
    """Test the full optimization dashboard."""
    print("\n=== Testing Optimization Dashboard ===")
    
    # Generate sample data
    results_df = generate_sample_optimization_results(n_params=5, n_results=100)
    
    # Create the dashboard
    output_path = Path("test_outputs/optimization_dashboard.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    create_optimization_dashboard(
        results_df,
        output_path=str(output_path)
    )
    
    print(f"Optimization dashboard saved to {output_path}")
    print(f"Opening {output_path} in browser...")
    webbrowser.open(str(output_path))

def run_all_tests():
    """Run all optimization visualization tests."""
    print("=== Running All Optimization Visualization Tests ===")
    
    # Make output directory
    os.makedirs("test_outputs", exist_ok=True)
    
    # Run all tests
    test_parameter_heatmap()
    test_parameter_impact_chart()
    test_parallel_coordinates_plot()
    test_optimization_dashboard()
    
    print("\n=== All tests completed! ===")
    print("Test outputs saved to the test_outputs directory")

if __name__ == "__main__":
    run_all_tests()
