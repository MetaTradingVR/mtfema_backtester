"""
Optimization visualization components for the MT 9 EMA Extension Strategy Backtester.

This module provides visualization tools for parameter optimization results.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def create_optimization_heatmap(results_df, param_x, param_y, metric='total_return', 
                               title="Parameter Optimization Results"):
    """
    Create a heatmap visualization for parameter optimization results.
    
    Args:
        results_df: DataFrame with optimization results
        param_x: Parameter name for x-axis
        param_y: Parameter name for y-axis
        metric: Performance metric to visualize
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if results_df.empty:
        logger.warning("No optimization results available for heatmap")
        return go.Figure()
    
    # Pivot the data for heatmap format
    try:
        pivot_df = results_df.pivot_table(
            index=param_y, 
            columns=param_x, 
            values=metric,
            aggfunc='mean'  # In case of duplicate parameter combinations
        )
        
        # Create the heatmap
        fig = px.imshow(
            pivot_df,
            labels=dict(x=param_x, y=param_y, color=metric),
            x=pivot_df.columns,
            y=pivot_df.index,
            color_continuous_scale='RdYlGn',
            aspect="auto",
            title=f"{title}: {metric}"
        )
        
        # Add text annotations
        annotations = []
        for i, y in enumerate(pivot_df.index):
            for j, x in enumerate(pivot_df.columns):
                value = pivot_df.iloc[i, j]
                if not pd.isna(value):
                    if metric.endswith('_pct') or metric in ['win_rate', 'total_return', 'max_drawdown']:
                        text = f"{value:.2f}%"
                    elif metric in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio']:
                        text = f"{value:.2f}"
                    else:
                        text = f"{value:.2f}"
                    
                    annotations.append({
                        'x': x,
                        'y': y,
                        'text': text,
                        'font': {'color': 'black' if 0.2 <= (value - pivot_df.values.min()) / (pivot_df.values.max() - pivot_df.values.min()) <= 0.8 else 'white'},
                        'showarrow': False
                    })
        
        fig.update_layout(annotations=annotations)
        
        # Improve layout
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, b=50, t=100, pad=4),
            coloraxis_colorbar=dict(
                title=metric,
                thicknessmode="pixels", thickness=20,
                lenmode="pixels", len=300,
                yanchor="top", y=1,
                ticks="outside"
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating optimization heatmap: {str(e)}")
        return go.Figure()

def create_parameter_impact_chart(results_df, metric='total_return', n_params=5, 
                                 title="Parameter Impact Analysis"):
    """
    Create a visualization showing the impact of each parameter on performance.
    
    Args:
        results_df: DataFrame with optimization results
        metric: Performance metric to analyze
        n_params: Number of top parameters to include
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if results_df.empty:
        logger.warning("No optimization results available for parameter impact analysis")
        return go.Figure()
    
    try:
        # Get parameter columns (exclude metrics)
        metric_cols = ['total_return', 'win_rate', 'profit_factor', 'max_drawdown', 
                      'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'avg_trade']
        param_cols = [col for col in results_df.columns if col not in metric_cols]
        
        # Calculate impact score for each parameter
        impact_scores = {}
        for param in param_cols:
            # Group by parameter and calculate mean and std of the metric
            grouped = results_df.groupby(param)[metric].agg(['mean', 'std'])
            # Impact score = standard deviation of means (higher = more impact)
            if not grouped['mean'].empty:
                impact_scores[param] = grouped['mean'].std()
        
        # Create DataFrame from impact scores
        impact_df = pd.DataFrame.from_dict(impact_scores, orient='index', 
                                        columns=['impact_score']).sort_values('impact_score', ascending=False)
        
        # Take top N parameters
        impact_df = impact_df.head(n_params)
        
        # Create the bar chart
        fig = px.bar(
            impact_df,
            y=impact_df.index,
            x='impact_score',
            orientation='h',
            title=f"{title}: {metric}",
            labels={'impact_score': 'Impact Score', 'index': 'Parameter'},
            color='impact_score',
            color_continuous_scale='Blues'
        )
        
        # Improve layout
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, b=50, t=100, pad=4),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating parameter impact chart: {str(e)}")
        return go.Figure()

def create_parallel_coordinates_plot(results_df, metric='total_return', top_n=50, 
                                    title="Parameter Combinations Analysis"):
    """
    Create a parallel coordinates plot for analyzing multiple parameter combinations.
    
    Args:
        results_df: DataFrame with optimization results
        metric: Performance metric to color by
        top_n: Number of top parameter combinations to include
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if results_df.empty:
        logger.warning("No optimization results available for parallel coordinates plot")
        return go.Figure()
    
    try:
        # Sort by the metric and take top N results
        sorted_df = results_df.sort_values(by=metric, ascending=False).head(top_n)
        
        # Get parameter columns (exclude metrics)
        metric_cols = ['total_return', 'win_rate', 'profit_factor', 'max_drawdown', 
                      'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'avg_trade']
        param_cols = [col for col in sorted_df.columns if col not in metric_cols]
        
        # Include the metric column as well
        dimensions = param_cols + [metric]
        
        # Create the parallel coordinates plot
        fig = px.parallel_coordinates(
            sorted_df,
            dimensions=dimensions,
            color=metric,
            color_continuous_scale='Viridis',
            title=f"{title}: Top {top_n} Combinations"
        )
        
        # Improve layout
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, b=50, t=100, pad=4),
            coloraxis_colorbar=dict(
                title=metric,
                thicknessmode="pixels", thickness=20,
                lenmode="pixels", len=300,
                yanchor="top", y=1,
                ticks="outside"
            )
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating parallel coordinates plot: {str(e)}")
        return go.Figure()

def create_optimization_dashboard(results_df, output_path=None):
    """
    Create a comprehensive optimization results dashboard.
    
    Args:
        results_df: DataFrame with optimization results
        output_path: Path to save the HTML dashboard
        
    Returns:
        HTML string or path to saved file
    """
    if results_df.empty:
        logger.warning("No optimization results available for dashboard")
        return None
    
    # Create individual components
    try:
        # Identify the top 2 most impactful parameters
        metric_cols = ['total_return', 'win_rate', 'profit_factor', 'max_drawdown', 
                      'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'avg_trade']
        param_cols = [col for col in results_df.columns if col not in metric_cols]
        
        # Calculate impact scores
        impact_scores = {}
        for param in param_cols:
            grouped = results_df.groupby(param)['total_return'].agg(['mean', 'std'])
            if not grouped['mean'].empty:
                impact_scores[param] = grouped['mean'].std()
        
        # Sort parameters by impact
        sorted_params = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create visualizations
        components = []
        
        # If we have at least 2 parameters, create a heatmap
        if len(sorted_params) >= 2:
            param_x, _ = sorted_params[0]
            param_y, _ = sorted_params[1]
            heatmap = create_optimization_heatmap(
                results_df, 
                param_x=param_x, 
                param_y=param_y, 
                metric='total_return',
                title="Parameter Optimization: Total Return"
            )
            components.append(heatmap)
            
            # Add a second heatmap for Sharpe Ratio
            if 'sharpe_ratio' in results_df.columns:
                heatmap2 = create_optimization_heatmap(
                    results_df, 
                    param_x=param_x, 
                    param_y=param_y, 
                    metric='sharpe_ratio',
                    title="Parameter Optimization: Sharpe Ratio"
                )
                components.append(heatmap2)
        
        # Add parameter impact chart
        impact_chart = create_parameter_impact_chart(
            results_df,
            metric='total_return',
            n_params=min(5, len(param_cols)),
            title="Parameter Impact on Total Return"
        )
        components.append(impact_chart)
        
        # Add parallel coordinates plot
        parallel_plot = create_parallel_coordinates_plot(
            results_df,
            metric='total_return',
            top_n=min(50, len(results_df)),
            title="Top Parameter Combinations"
        )
        components.append(parallel_plot)
        
        # Combine into a single dashboard
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Optimization Results Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .chart-container {
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                    padding: 15px;
                }
                .chart {
                    width: 100%;
                    height: 500px;
                }
                h1 {
                    color: #333;
                }
                h2 {
                    color: #555;
                    margin-top: 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MT 9 EMA Strategy Optimization Results</h1>
                    <p>Generated on {}</p>
                </div>
        """.format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add each component to the dashboard
        for i, component in enumerate(components):
            dashboard_html += f"""
                <div class="chart-container">
                    <div id="chart{i}" class="chart"></div>
                </div>
                <script>
                    var data{i} = {component.to_json()};
                    Plotly.newPlot('chart{i}', data{i}.data, data{i}.layout);
                </script>
            """
        
        dashboard_html += """
            </div>
        </body>
        </html>
        """
        
        # Save to file if output path is provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            logger.info(f"Optimization dashboard saved to {output_path}")
            return str(output_path)
        
        return dashboard_html
        
    except Exception as e:
        logger.error(f"Error creating optimization dashboard: {str(e)}")
        return None
