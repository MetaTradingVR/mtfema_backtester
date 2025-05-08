"""
Live trading dashboard for the MT 9 EMA Extension Strategy.

This module provides real-time visualization for monitoring live trading
performance with Tradovate and Rithmic brokers.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import threading
import time
import logging
from pathlib import Path
import os
import queue

from .dashboard_components import (
    create_equity_curve_component,
    create_trade_distribution_component,
    create_metrics_summary_component
)

logger = logging.getLogger(__name__)

class LiveTradingDashboard:
    """
    Interactive dashboard for monitoring live trading performance.
    
    This dashboard shows real-time equity curves, positions, signals,
    and market data across multiple timeframes.
    """
    
    def __init__(self, live_trader, update_interval=2000, port=8051):
        """
        Initialize the live trading dashboard.
        
        Args:
            live_trader: LiveTrader instance
            update_interval: Dashboard update interval in milliseconds
            port: Port to run the dashboard on
        """
        self.live_trader = live_trader
        self.update_interval = update_interval
        self.port = port
        
        # Data storage for dashboard
        self.equity_data = pd.DataFrame(columns=['datetime', 'balance'])
        self.trades = pd.DataFrame(columns=[
            'id', 'symbol', 'direction', 'entry_time', 'exit_time',
            'entry_price', 'exit_price', 'position_size', 'pnl',
            'status', 'timeframe'
        ])
        self.signals = []
        self.active_positions = {}
        self.market_data = {}
        
        # Message queue for dashboard updates
        self.update_queue = queue.Queue()
        
        # Register callbacks with live trader
        self._register_callbacks()
        
        # Create the dashboard app
        self.app = self._create_dashboard()
        self.server = None
        self.thread = None
    
    def _register_callbacks(self):
        """Register callbacks with the live trader."""
        # Add signal callback
        self.live_trader.add_signal_callback(self._on_signal)
        
        # Add order callback
        self.live_trader.add_order_callback(self._on_order_update)
        
        # Add position callback
        self.live_trader.add_position_callback(self._on_position_update)
    
    def _on_signal(self, signal):
        """Handle new trading signal."""
        try:
            # Add timestamp if not present
            if 'datetime' not in signal:
                signal['datetime'] = datetime.now()
            
            # Add to signals list
            self.signals.append(signal)
            
            # Limit signals list to last 100 signals
            if len(self.signals) > 100:
                self.signals = self.signals[-100:]
            
            # Queue dashboard update
            self.update_queue.put(('signals', signal))
            
        except Exception as e:
            logger.error(f"Error handling signal: {str(e)}")
    
    def _on_order_update(self, order):
        """Handle order updates."""
        try:
            # Queue dashboard update
            self.update_queue.put(('order', order))
            
        except Exception as e:
            logger.error(f"Error handling order update: {str(e)}")
    
    def _on_position_update(self, position):
        """Handle position updates."""
        try:
            position_id = position.get('id')
            
            # Update active positions
            if position.get('status') == 'open':
                self.active_positions[position_id] = position
            elif position_id in self.active_positions:
                # Position closed, remove from active positions
                # and add to completed trades
                closed_position = self.active_positions.pop(position_id)
                
                # Create trade record
                trade = {
                    'id': position_id,
                    'symbol': position.get('symbol'),
                    'direction': position.get('direction'),
                    'entry_time': closed_position.get('timestamp', datetime.now() - timedelta(minutes=30)),
                    'exit_time': position.get('timestamp', datetime.now()),
                    'entry_price': closed_position.get('entry_price', 0),
                    'exit_price': position.get('exit_price', 0),
                    'position_size': position.get('quantity', 0),
                    'pnl': position.get('realized_pl', 0),
                    'status': 'closed',
                    'timeframe': position.get('timeframe', '1h')
                }
                
                # Add to trades DataFrame
                self.trades = pd.concat([
                    self.trades, 
                    pd.DataFrame([trade])
                ], ignore_index=True)
            
            # Update equity data
            account_info = self.live_trader.broker.get_account_info()
            balance = account_info.get('balance', 0.0)
            
            # Add to equity DataFrame
            new_equity = pd.DataFrame([{
                'datetime': datetime.now(),
                'balance': balance
            }])
            
            self.equity_data = pd.concat([
                self.equity_data, 
                new_equity
            ], ignore_index=True)
            
            # Queue dashboard update
            self.update_queue.put(('position', position))
            
        except Exception as e:
            logger.error(f"Error handling position update: {str(e)}")
    
    def _create_dashboard(self):
        """Create the Dash application for the dashboard."""
        app = dash.Dash(__name__, suppress_callback_exceptions=True)
        
        # Define the dashboard layout
        app.layout = html.Div([
            # Header
            html.Div([
                html.H1("MT 9 EMA Strategy - Live Trading Dashboard"),
                html.Div([
                    html.Button("Start Trading", id="start-button", className="control-button"),
                    html.Button("Stop Trading", id="stop-button", className="control-button"),
                    dcc.Interval(
                        id='interval-component',
                        interval=self.update_interval,
                        n_intervals=0
                    )
                ], className="controls")
            ], className="header"),
            
            # Main content
            html.Div([
                # Left column - Performance metrics
                html.Div([
                    html.Div([
                        html.H3("Account Status"),
                        html.Div(id="account-info-container")
                    ], className="card"),
                    html.Div([
                        html.H3("Performance Metrics"),
                        html.Div(id="metrics-container")
                    ], className="card"),
                    html.Div([
                        html.H3("Active Positions"),
                        html.Div(id="positions-table-container")
                    ], className="card")
                ], className="column left-column"),
                
                # Right column - Charts
                html.Div([
                    html.Div([
                        html.H3("Equity Curve"),
                        dcc.Graph(id="equity-chart")
                    ], className="card"),
                    html.Div([
                        html.H3("Recent Signals"),
                        dcc.Graph(id="signals-chart")
                    ], className="card"),
                    html.Div([
                        html.H3("Trade Distribution"),
                        dcc.Graph(id="trade-distribution")
                    ], className="card")
                ], className="column right-column")
            ], className="content"),
            
            # Hidden components for storing data
            html.Div([
                dcc.Store(id="equity-data-store"),
                dcc.Store(id="trades-data-store"),
                dcc.Store(id="signals-data-store"),
                dcc.Store(id="positions-data-store")
            ], style={"display": "none"})
            
        ], className="container")
        
        # Define the callback for updating data stores
        @app.callback(
            [Output("equity-data-store", "data"),
             Output("trades-data-store", "data"),
             Output("signals-data-store", "data"),
             Output("positions-data-store", "data")],
            [Input("interval-component", "n_intervals")]
        )
        def update_data_stores(n_intervals):
            """Update data stores with latest information."""
            # Process any queued updates
            while not self.update_queue.empty():
                try:
                    update_type, data = self.update_queue.get_nowait()
                    logger.debug(f"Processing dashboard update: {update_type}")
                except queue.Empty:
                    break
            
            # Convert DataFrames to JSON serializable format
            equity_data = self.equity_data.to_dict("records")
            trades_data = self.trades.to_dict("records")
            signals_data = self.signals  # Already a list of dicts
            positions_data = list(self.active_positions.values())
            
            return equity_data, trades_data, signals_data, positions_data
        
        # Define callback for updating equity chart
        @app.callback(
            Output("equity-chart", "figure"),
            [Input("equity-data-store", "data")]
        )
        def update_equity_chart(equity_data):
            """Update the equity curve chart."""
            if not equity_data:
                return go.Figure()
            
            # Convert to DataFrame
            df = pd.DataFrame(equity_data)
            
            # Create equity chart
            fig = create_equity_curve_component(df, "Real-time Equity Curve")
            
            # Auto-resize
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            
            return fig
        
        # Define callback for updating signals chart
        @app.callback(
            Output("signals-chart", "figure"),
            [Input("signals-data-store", "data")]
        )
        def update_signals_chart(signals_data):
            """Update the recent signals chart."""
            if not signals_data:
                return go.Figure()
            
            # Take the last 20 signals
            recent_signals = signals_data[-20:]
            
            # Create a figure
            fig = go.Figure()
            
            # Add signals as a scatter plot
            signal_times = [s.get('datetime', datetime.now()) 
                           if isinstance(s.get('datetime'), (str, datetime)) 
                           else datetime.now() for s in recent_signals]
            
            signal_directions = [1 if s.get('direction', '').lower() == 'long' else -1 
                              for s in recent_signals]
            
            signal_timeframes = [s.get('timeframe', '1h') for s in recent_signals]
            
            # Create hover text
            hover_texts = []
            for s in recent_signals:
                direction = s.get('direction', 'unknown')
                tf = s.get('timeframe', 'unknown')
                symbol = s.get('symbol', 'unknown')
                confidence = s.get('confidence', 'unknown')
                hover_texts.append(
                    f"Direction: {direction}<br>"
                    f"Timeframe: {tf}<br>"
                    f"Symbol: {symbol}<br>"
                    f"Confidence: {confidence}"
                )
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=signal_times,
                y=signal_directions,
                mode='markers',
                marker=dict(
                    size=12,
                    color=['green' if d > 0 else 'red' for d in signal_directions],
                    symbol=['triangle-up' if d > 0 else 'triangle-down' for d in signal_directions],
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                text=hover_texts,
                hoverinfo='text'
            ))
            
            # Add horizontal lines for long/short
            fig.add_shape(
                type="line", line=dict(dash='dash', width=1, color="green"),
                x0=min(signal_times), x1=max(signal_times) if signal_times else datetime.now(),
                y0=1, y1=1
            )
            
            fig.add_shape(
                type="line", line=dict(dash='dash', width=1, color="red"),
                x0=min(signal_times), x1=max(signal_times) if signal_times else datetime.now(),
                y0=-1, y1=-1
            )
            
            # Update layout
            fig.update_layout(
                title="Recent Trading Signals",
                xaxis_title="Time",
                yaxis_title="Direction",
                yaxis=dict(
                    tickvals=[-1, 1],
                    ticktext=["Short", "Long"],
                    range=[-1.5, 1.5]
                ),
                height=300,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            
            return fig
        
        # Define callback for updating trade distribution
        @app.callback(
            Output("trade-distribution", "figure"),
            [Input("trades-data-store", "data")]
        )
        def update_trade_distribution(trades_data):
            """Update the trade distribution chart."""
            if not trades_data:
                return go.Figure()
            
            # Convert to DataFrame
            df = pd.DataFrame(trades_data)
            
            # Create trade distribution
            fig = create_trade_distribution_component(df, "Trade P&L Distribution")
            
            # Auto-resize
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
            
            return fig
        
        # Define callback for updating account info
        @app.callback(
            Output("account-info-container", "children"),
            [Input("equity-data-store", "data"),
             Input("positions-data-store", "data")]
        )
        def update_account_info(equity_data, positions_data):
            """Update the account information card."""
            try:
                # Get account info
                account_info = self.live_trader.broker.get_account_info()
                
                # Calculate total positions value
                positions_value = sum(p.get('market_value', 0) for p in positions_data) if positions_data else 0
                
                # Create card content
                return html.Div([
                    html.Div([
                        html.Div("Balance", className="label"),
                        html.Div(f"${account_info.get('balance', 0):.2f}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Available", className="label"),
                        html.Div(f"${account_info.get('available', 0):.2f}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Positions Value", className="label"),
                        html.Div(f"${positions_value:.2f}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Broker", className="label"),
                        html.Div(f"{self.live_trader.broker.__class__.__name__}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Status", className="label"),
                        html.Div(
                            "Running" if self.live_trader.running else "Stopped", 
                            className="value status-value",
                            style={"color": "green" if self.live_trader.running else "red"}
                        )
                    ], className="info-item")
                ], className="account-info")
            except Exception as e:
                logger.error(f"Error updating account info: {str(e)}")
                return html.Div("Error loading account information")
        
        # Define callback for updating metrics
        @app.callback(
            Output("metrics-container", "children"),
            [Input("trades-data-store", "data")]
        )
        def update_metrics(trades_data):
            """Update the performance metrics card."""
            if not trades_data:
                return html.Div("No trades completed yet")
            
            try:
                # Convert to DataFrame
                df = pd.DataFrame(trades_data)
                
                # Calculate metrics
                total_trades = len(df)
                winning_trades = len(df[df['pnl'] > 0])
                win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
                
                total_profit = df[df['pnl'] > 0]['pnl'].sum()
                total_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
                profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
                
                avg_profit = df[df['pnl'] > 0]['pnl'].mean() if len(df[df['pnl'] > 0]) > 0 else 0
                avg_loss = df[df['pnl'] < 0]['pnl'].mean() if len(df[df['pnl'] < 0]) > 0 else 0
                
                # Create metrics summary
                return html.Div([
                    html.Div([
                        html.Div("Total Trades", className="label"),
                        html.Div(f"{total_trades}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Win Rate", className="label"),
                        html.Div(f"{win_rate:.1f}%", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Profit Factor", className="label"),
                        html.Div(
                            f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞", 
                            className="value"
                        )
                    ], className="info-item"),
                    html.Div([
                        html.Div("Avg Win", className="label"),
                        html.Div(f"${avg_profit:.2f}", className="value")
                    ], className="info-item"),
                    html.Div([
                        html.Div("Avg Loss", className="label"),
                        html.Div(f"${avg_loss:.2f}", className="value")
                    ], className="info-item")
                ], className="metrics-summary")
            except Exception as e:
                logger.error(f"Error updating metrics: {str(e)}")
                return html.Div("Error calculating metrics")
        
        # Define callback for updating positions table
        @app.callback(
            Output("positions-table-container", "children"),
            [Input("positions-data-store", "data")]
        )
        def update_positions_table(positions_data):
            """Update the active positions table."""
            if not positions_data:
                return html.Div("No active positions")
            
            try:
                # Create positions table
                return html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Symbol"),
                            html.Th("Direction"),
                            html.Th("Size"),
                            html.Th("Entry"),
                            html.Th("Current"),
                            html.Th("P&L")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(p.get('symbol', '')),
                            html.Td(p.get('direction', '').capitalize()),
                            html.Td(p.get('quantity', 0)),
                            html.Td(f"${p.get('entry_price', 0):.2f}"),
                            html.Td(f"${p.get('current_price', 0):.2f}"),
                            html.Td(
                                f"${p.get('unrealized_pl', 0):.2f}",
                                style={"color": "green" if p.get('unrealized_pl', 0) > 0 else "red"}
                            )
                        ]) for p in positions_data
                    ])
                ], className="positions-table")
            except Exception as e:
                logger.error(f"Error updating positions table: {str(e)}")
                return html.Div("Error loading positions")
        
        # Define callbacks for start/stop buttons
        @app.callback(
            Output("start-button", "disabled"),
            [Input("start-button", "n_clicks")]
        )
        def start_trading(n_clicks):
            """Start the live trader."""
            if n_clicks is not None and n_clicks > 0:
                try:
                    if not self.live_trader.running:
                        self.live_trader.start()
                        logger.info("Live trader started from dashboard")
                    return True
                except Exception as e:
                    logger.error(f"Error starting live trader: {str(e)}")
            return False
        
        @app.callback(
            Output("stop-button", "disabled"),
            [Input("stop-button", "n_clicks")]
        )
        def stop_trading(n_clicks):
            """Stop the live trader."""
            if n_clicks is not None and n_clicks > 0:
                try:
                    if self.live_trader.running:
                        self.live_trader.stop()
                        logger.info("Live trader stopped from dashboard")
                    return True
                except Exception as e:
                    logger.error(f"Error stopping live trader: {str(e)}")
            return False
        
        # Add custom CSS
        app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>MT 9 EMA Strategy - Live Trading Dashboard</title>
                {%css%}
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f5f5f5;
                    }
                    .container {
                        max-width: 1400px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 20px;
                        background-color: #343a40;
                        padding: 15px 20px;
                        border-radius: 5px;
                        color: white;
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 24px;
                    }
                    .controls {
                        display: flex;
                        gap: 10px;
                    }
                    .control-button {
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                    }
                    .control-button:first-child {
                        background-color: #28a745;
                        color: white;
                    }
                    .control-button:last-child {
                        background-color: #dc3545;
                        color: white;
                    }
                    .content {
                        display: flex;
                        gap: 20px;
                    }
                    .column {
                        flex: 1;
                    }
                    .left-column {
                        flex: 0 0 300px;
                    }
                    .card {
                        background-color: white;
                        border-radius: 5px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        padding: 15px;
                        margin-bottom: 20px;
                    }
                    .card h3 {
                        margin-top: 0;
                        margin-bottom: 15px;
                        color: #343a40;
                        font-size: 16px;
                        padding-bottom: 10px;
                        border-bottom: 1px solid #eee;
                    }
                    .account-info, .metrics-summary {
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 10px;
                    }
                    .info-item {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 8px 0;
                        border-bottom: 1px solid #f5f5f5;
                    }
                    .info-item:last-child {
                        border-bottom: none;
                    }
                    .label {
                        font-weight: 500;
                        color: #666;
                    }
                    .value {
                        font-weight: bold;
                        color: #333;
                    }
                    .positions-table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    .positions-table th,
                    .positions-table td {
                        padding: 8px;
                        text-align: left;
                        border-bottom: 1px solid #eee;
                    }
                    .positions-table th {
                        font-weight: 500;
                        color: #666;
                    }
                    
                    @media (max-width: 1000px) {
                        .content {
                            flex-direction: column;
                        }
                        .left-column {
                            flex: 1;
                        }
                    }
                </style>
                {%favicon%}
                {%metas%}
                {%title%}
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        
        return app
    
    def start(self, open_browser=True):
        """
        Start the dashboard server.
        
        Args:
            open_browser: Whether to automatically open browser
        """
        def run_server():
            self.server = self.app.server
            self.app.run_server(debug=False, port=self.port, use_reloader=False)
        
        if self.thread is None or not self.thread.is_alive():
            logger.info(f"Starting live trading dashboard on port {self.port}")
            self.thread = threading.Thread(target=run_server)
            self.thread.daemon = True
            self.thread.start()
            
            # Wait a bit for the server to start
            time.sleep(1.0)
            
            # Open browser if requested
            if open_browser:
                url = f"http://localhost:{self.port}"
                logger.info(f"Opening browser to {url}")
                threading.Thread(target=lambda: webbrowser.open(url)).start()
        else:
            logger.warning("Dashboard server is already running")
    
    def stop(self):
        """Stop the dashboard server."""
        if self.thread and self.thread.is_alive():
            logger.info("Stopping live trading dashboard")
            # There's no clean way to stop a Dash server in a thread,
            # but since it's a daemon thread, it will be terminated
            # when the main program exits
            self.thread = None
        else:
            logger.warning("Dashboard server is not running")

def create_live_trading_dashboard(live_trader, port=8051, open_browser=True):
    """
    Create and start a live trading dashboard.
    
    Args:
        live_trader: LiveTrader instance
        port: Port to run the dashboard on
        open_browser: Whether to automatically open browser
        
    Returns:
        LiveTradingDashboard instance
    """
    dashboard = LiveTradingDashboard(live_trader, port=port)
    dashboard.start(open_browser=open_browser)
    return dashboard
