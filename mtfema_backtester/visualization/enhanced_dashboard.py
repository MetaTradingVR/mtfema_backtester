"""
Enhanced dashboard for the MT 9 EMA Extension Strategy Backtester.

This module provides a more comprehensive interactive dashboard
for visualizing backtest results.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import webbrowser
import threading
import time

from .dashboard_components import (
    create_equity_curve_component,
    create_trade_distribution_component,
    create_trade_calendar_component,
    create_drawdown_chart,
    create_timeframe_performance_component,
    create_metrics_summary_component
)

logger = logging.getLogger(__name__)

def create_enhanced_dashboard(trades_df, equity_curve, metrics, output_path=None):
    """
    Create a comprehensive enhanced dashboard with multiple visualizations.
    
    Args:
        trades_df: DataFrame with trade results
        equity_curve: DataFrame or list with equity curve data
        metrics: Dictionary of performance metrics
        output_path: Path to save HTML dashboard
        
    Returns:
        Dashboard HTML or path to saved file
    """
    if trades_df.empty:
        logger.warning("No trade data available for dashboard")
        return None
    
    # Create components
    equity_fig = create_equity_curve_component(equity_curve, "Equity Growth & Drawdown")
    trade_dist_fig = create_trade_distribution_component(trades_df, "Trade P&L Distribution")
    calendar_fig = create_trade_calendar_component(trades_df, "Monthly Performance")
    drawdown_fig = create_drawdown_chart(equity_curve, "Drawdown Analysis")
    timeframe_fig = create_timeframe_performance_component(trades_df, "Performance by Timeframe")
    metrics_html = create_metrics_summary_component(metrics)
    
    # Create combined dashboard
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MT 9 EMA Strategy Performance Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .dashboard-container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background-color: #343a40; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .metrics-container {{ margin-bottom: 20px; }}
            .chart-container {{ background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 15px; margin-bottom: 20px; }}
            .row {{ display: flex; flex-wrap: wrap; margin: 0 -10px; }}
            .col {{ flex: 1; padding: 0 10px; min-width: 300px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #6c757d; font-size: 14px; }}
            @media (max-width: 768px) {{ .col {{ min-width: 100%; }} }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="header">
                <h1>MT 9 EMA Extension Strategy Performance Dashboard</h1>
            </div>
            
            <div class="metrics-container">
                {metrics_html}
            </div>
            
            <div class="chart-container">
                <div id="equity-curve"></div>
            </div>
            
            <div class="row">
                <div class="col">
                    <div class="chart-container">
                        <div id="drawdown-chart"></div>
                    </div>
                </div>
                <div class="col">
                    <div class="chart-container">
                        <div id="timeframe-performance"></div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col">
                    <div class="chart-container">
                        <div id="trade-distribution"></div>
                    </div>
                </div>
                <div class="col">
                    <div class="chart-container">
                        <div id="monthly-performance"></div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>MT 9 EMA Extension Strategy Backtester &copy; {pd.Timestamp.now().year}</p>
            </div>
        </div>
        
        <script>
            // Render plots
            Plotly.newPlot('equity-curve', {equity_fig.to_json()['data']}, {equity_fig.to_json()['layout']});
            Plotly.newPlot('trade-distribution', {trade_dist_fig.to_json()['data']}, {trade_dist_fig.to_json()['layout']});
            Plotly.newPlot('monthly-performance', {calendar_fig.to_json()['data']}, {calendar_fig.to_json()['layout']});
            Plotly.newPlot('drawdown-chart', {drawdown_fig.to_json()['data']}, {drawdown_fig.to_json()['layout']});
            Plotly.newPlot('timeframe-performance', {timeframe_fig.to_json()['data']}, {timeframe_fig.to_json()['layout']});
        </script>
    </body>
    </html>
    """
    
    # Save to file if output path provided
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            logger.info(f"Dashboard saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving dashboard: {str(e)}")
    
    return dashboard_html

def create_interactive_dashboard(trades_df, equity_curve, metrics, port=8050, open_browser=True):
    """
    Create an interactive Dash web application for performance analysis.
    
    Args:
        trades_df: DataFrame with trade results
        equity_curve: DataFrame or list with equity curve data
        metrics: Dictionary of performance metrics
        port: Port to run the dash app on
        open_browser: Whether to automatically open browser
        
    Returns:
        Dash application instance
    """
    if trades_df.empty:
        logger.warning("No trade data available for dashboard")
        return None
    
    # Convert equity curve if it's a list
    if isinstance(equity_curve, list):
        equity_df = pd.DataFrame(equity_curve, columns=['datetime', 'balance'])
    else:
        equity_df = equity_curve.copy()
        
    # Initialize Dash app
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    
    # Create initial figures
    equity_fig = create_equity_curve_component(equity_df, "Equity Growth & Drawdown")
    trade_dist_fig = create_trade_distribution_component(trades_df, "Trade P&L Distribution")
    calendar_fig = create_trade_calendar_component(trades_df, "Monthly Performance")
    drawdown_fig = create_drawdown_chart(equity_df, "Drawdown Analysis")
    timeframe_fig = create_timeframe_performance_component(trades_df, "Performance by Timeframe")
    metrics_html = create_metrics_summary_component(metrics)
    
    # Define app layout
    app.layout = html.Div([
        html.Div([
            html.H1("MT 9 EMA Extension Strategy Performance Dashboard"),
            html.P("Interactive analysis of backtest results")
        ], className="header"),
        
        html.Div([
            html.Div([
                dcc.Tabs([
                    dcc.Tab(label="Overview", children=[
                        html.Div([
                            html.Div([
                                html.H3("Performance Metrics", className="panel-title"),
                                html.Div(
                                    dangerouslySetInnerHTML={"__html": metrics_html},
                                    className="metrics-panel"
                                )
                            ], className="metrics-container"),
                            
                            html.Div([
                                html.H3("Equity Curve", className="panel-title"),
                                dcc.Graph(figure=equity_fig, id="equity-graph")
                            ], className="chart-container"),
                            
                            html.Div(className="row", children=[
                                html.Div([
                                    html.H3("Drawdown Analysis", className="panel-title"),
                                    dcc.Graph(figure=drawdown_fig, id="drawdown-graph")
                                ], className="col chart-container"),
                                
                                html.Div([
                                    html.H3("Trade Distribution", className="panel-title"),
                                    dcc.Graph(figure=trade_dist_fig, id="trade-dist-graph")
                                ], className="col chart-container")
                            ])
                        ])
                    ]),
                    
                    dcc.Tab(label="Time Analysis", children=[
                        html.Div([
                            html.Div([
                                html.H3("Monthly Performance", className="panel-title"),
                                dcc.Graph(figure=calendar_fig, id="calendar-graph")
                            ], className="chart-container"),
                            
                            html.Div([
                                html.H3("Timeframe Performance", className="panel-title"),
                                dcc.Graph(figure=timeframe_fig, id="timeframe-graph")
                            ], className="chart-container"),
                        ])
                    ]),
                    
                    dcc.Tab(label="Trade Details", children=[
                        html.Div([
                            html.H3("Individual Trades", className="panel-title"),
                            html.Div(id="trades-table-container", className="table-container")
                        ], className="chart-container")
                    ])
                ])
            ], className="dashboard-content")
        ], className="dashboard-container"),
        
        html.Footer([
            html.P(f"MT 9 EMA Extension Strategy Backtester © {pd.Timestamp.now().year}")
        ], className="footer")
    ])
    
    # Add callback for trades table
    @app.callback(
        Output("trades-table-container", "children"),
        Input("trades-table-container", "id")
    )
    def populate_trades_table(_):
        if trades_df.empty:
            return html.P("No trade data available")
            
        # Prepare a clean version of the trades dataframe for display
        display_cols = [
            'id', 'entry_time', 'exit_time', 'timeframe', 'direction', 
            'entry_price', 'exit_price', 'profit_loss'
        ]
        
        display_df = trades_df.copy()
        
        # Rename columns for display if they exist with different names
        if 'pnl' in display_df.columns and 'profit_loss' not in display_df.columns:
            display_df['profit_loss'] = display_df['pnl']
        
        # Only keep columns that exist
        display_cols = [c for c in display_cols if c in display_df.columns]
        display_df = display_df[display_cols]
        
        # Format the table
        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in display_df.columns])] +
            
            # Body
            [
                html.Tr([
                    html.Td(display_df.iloc[i][col]) for col in display_df.columns
                ]) for i in range(min(len(display_df), 100))  # Limit to 100 rows for performance
            ],
            className="trades-table"
        )
    
    # Function to open browser after app starts
    def open_browser_tab():
        time.sleep(2)  # Wait for app to start
        webbrowser.open_new_tab(f"http://localhost:{port}")
    
    # Start the server
    if open_browser:
        threading.Thread(target=open_browser_tab).start()
    
    return app

def run_dashboard_server(trades_df, equity_curve, metrics, port=8050):
    """
    Create and run an interactive dashboard server.
    
    Args:
        trades_df: DataFrame with trade results
        equity_curve: DataFrame or list with equity curve data
        metrics: Dictionary of performance metrics
        port: Port to run the server on
    """
    app = create_interactive_dashboard(trades_df, equity_curve, metrics, port=port)
    if app:
        app.run_server(debug=False, port=port)
    else:
        logger.error("Failed to create interactive dashboard")
