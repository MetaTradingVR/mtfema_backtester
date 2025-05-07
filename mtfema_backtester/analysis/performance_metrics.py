"""
Performance metrics for backtest analysis

This module contains functions for calculating and analyzing backtest results.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Calculate and analyze trading performance metrics from backtest results
    """
    
    def __init__(self, trades_df=None, equity_curve=None):
        """
        Initialize the PerformanceMetrics calculator
        
        Parameters:
        -----------
        trades_df : pandas.DataFrame, optional
            DataFrame with trade details
        equity_curve : pandas.Series, optional
            Series with equity curve
        """
        self.trades_df = trades_df
        self.equity_curve = equity_curve
        self.metrics = {}
        
        # Calculate metrics if data is provided
        if trades_df is not None:
            self.calculate_metrics()
    
    def calculate_metrics(self, trades_df=None):
        """
        Calculate performance metrics from trade data
        
        Parameters:
        -----------
        trades_df : pandas.DataFrame, optional
            DataFrame with trade details, if not provided, uses the instance's trades_df
            
        Returns:
        --------
        dict
            Dictionary with performance metrics
        """
        if trades_df is not None:
            self.trades_df = trades_df
        
        if self.trades_df is None or len(self.trades_df) == 0:
            logger.warning("No trade data provided for metric calculation")
            return {}
        
        try:
            # Basic trade statistics
            self.metrics['total_trades'] = len(self.trades_df)
            win_mask = self.trades_df['profit'] > 0
            loss_mask = self.trades_df['profit'] < 0
            self.metrics['winning_trades'] = win_mask.sum()
            self.metrics['losing_trades'] = loss_mask.sum()
            
            # Win rate
            self.metrics['win_rate'] = self.metrics['winning_trades'] / self.metrics['total_trades'] if self.metrics['total_trades'] > 0 else 0.0
            
            # Profit metrics
            self.metrics['total_profit'] = self.trades_df['profit'].sum()
            self.metrics['gross_profit'] = self.trades_df.loc[win_mask, 'profit'].sum() if win_mask.any() else 0.0
            self.metrics['gross_loss'] = self.trades_df.loc[loss_mask, 'profit'].sum() if loss_mask.any() else 0.0
            
            # Average profit/loss
            self.metrics['avg_profit'] = self.trades_df['profit'].mean()
            self.metrics['avg_win'] = self.trades_df.loc[win_mask, 'profit'].mean() if win_mask.any() else 0.0
            self.metrics['avg_loss'] = self.trades_df.loc[loss_mask, 'profit'].mean() if loss_mask.any() else 0.0
            
            # Profit factor
            self.metrics['profit_factor'] = abs(self.metrics['gross_profit'] / self.metrics['gross_loss']) if self.metrics['gross_loss'] != 0 else float('inf')
            
            # Max drawdown
            if self.equity_curve is not None:
                self.metrics['max_drawdown'], self.metrics['max_drawdown_pct'] = self._calculate_max_drawdown()
            
            # Risk metrics
            if 'risk' in self.trades_df.columns:
                self.metrics['avg_risk'] = self.trades_df['risk'].mean()
                self.metrics['total_risk'] = self.trades_df['risk'].sum()
                risk_mask = self.trades_df['risk'] > 0
                if risk_mask.any():
                    self.metrics['reward_risk_ratio'] = self.metrics['avg_profit'] / self.trades_df.loc[risk_mask, 'risk'].mean()
                else:
                    self.metrics['reward_risk_ratio'] = float('nan')
            
            # Duration metrics
            if 'duration' in self.trades_df.columns:
                self.metrics['avg_duration'] = self.trades_df['duration'].mean()
                self.metrics['avg_win_duration'] = self.trades_df.loc[win_mask, 'duration'].mean() if win_mask.any() else 0.0
                self.metrics['avg_loss_duration'] = self.trades_df.loc[loss_mask, 'duration'].mean() if loss_mask.any() else 0.0
            
            # Trade direction metrics
            if 'direction' in self.trades_df.columns:
                long_mask = self.trades_df['direction'] == 'long'
                short_mask = self.trades_df['direction'] == 'short'
                
                self.metrics['long_trades'] = long_mask.sum()
                self.metrics['short_trades'] = short_mask.sum()
                
                self.metrics['long_win_rate'] = self.trades_df.loc[long_mask & win_mask].shape[0] / long_mask.sum() if long_mask.sum() > 0 else 0.0
                self.metrics['short_win_rate'] = self.trades_df.loc[short_mask & win_mask].shape[0] / short_mask.sum() if short_mask.sum() > 0 else 0.0
                
                self.metrics['long_profit'] = self.trades_df.loc[long_mask, 'profit'].sum()
                self.metrics['short_profit'] = self.trades_df.loc[short_mask, 'profit'].sum()
            
            # Timeframe metrics
            if 'timeframe' in self.trades_df.columns:
                timeframes = self.trades_df['timeframe'].unique()
                for tf in timeframes:
                    tf_mask = self.trades_df['timeframe'] == tf
                    tf_win_mask = tf_mask & win_mask
                    
                    self.metrics[f'{tf}_trades'] = tf_mask.sum()
                    self.metrics[f'{tf}_win_rate'] = tf_win_mask.sum() / tf_mask.sum() if tf_mask.sum() > 0 else 0.0
                    self.metrics[f'{tf}_profit'] = self.trades_df.loc[tf_mask, 'profit'].sum()
            
            logger.info(f"Calculated {len(self.metrics)} performance metrics")
            return self.metrics
        
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _calculate_max_drawdown(self):
        """
        Calculate maximum drawdown from equity curve
        
        Returns:
        --------
        tuple
            (max_drawdown_amount, max_drawdown_percentage)
        """
        if self.equity_curve is None or len(self.equity_curve) == 0:
            return 0.0, 0.0
        
        # Calculate running maximum
        running_max = self.equity_curve.cummax()
        
        # Calculate drawdown in currency amount
        drawdown = self.equity_curve - running_max
        max_drawdown = drawdown.min()
        
        # Calculate drawdown as percentage
        drawdown_pct = drawdown / running_max
        max_drawdown_pct = drawdown_pct.min()
        
        return abs(max_drawdown), abs(max_drawdown_pct)
    
    def get_summary(self, include_timeframes=True):
        """
        Get summary of performance metrics
        
        Parameters:
        -----------
        include_timeframes : bool
            Whether to include timeframe-specific metrics
            
        Returns:
        --------
        str
            Formatted summary string
        """
        if not self.metrics:
            return "No metrics available. Call calculate_metrics() first."
        
        summary = []
        summary.append("=== Performance Summary ===")
        summary.append(f"Total Trades: {self.metrics.get('total_trades', 0)}")
        summary.append(f"Win Rate: {self.metrics.get('win_rate', 0):.2%}")
        summary.append(f"Profit Factor: {self.metrics.get('profit_factor', 0):.2f}")
        summary.append(f"Total Profit: {self.metrics.get('total_profit', 0):.2f}")
        summary.append(f"Average Profit: {self.metrics.get('avg_profit', 0):.2f}")
        
        if 'max_drawdown' in self.metrics:
            summary.append(f"Max Drawdown: {self.metrics.get('max_drawdown', 0):.2f} ({self.metrics.get('max_drawdown_pct', 0):.2%})")
        
        if 'reward_risk_ratio' in self.metrics:
            summary.append(f"Reward-to-Risk Ratio: {self.metrics.get('reward_risk_ratio', 0):.2f}")
        
        if 'direction' in self.trades_df.columns:
            summary.append("\n=== Direction Analysis ===")
            summary.append(f"Long Trades: {self.metrics.get('long_trades', 0)} (Win Rate: {self.metrics.get('long_win_rate', 0):.2%})")
            summary.append(f"Short Trades: {self.metrics.get('short_trades', 0)} (Win Rate: {self.metrics.get('short_win_rate', 0):.2%})")
            summary.append(f"Long Profit: {self.metrics.get('long_profit', 0):.2f}")
            summary.append(f"Short Profit: {self.metrics.get('short_profit', 0):.2f}")
        
        if include_timeframes and 'timeframe' in self.trades_df.columns:
            summary.append("\n=== Timeframe Analysis ===")
            timeframes = self.trades_df['timeframe'].unique()
            for tf in timeframes:
                summary.append(f"{tf} Trades: {self.metrics.get(f'{tf}_trades', 0)} (Win Rate: {self.metrics.get(f'{tf}_win_rate', 0):.2%})")
                summary.append(f"{tf} Profit: {self.metrics.get(f'{tf}_profit', 0):.2f}")
        
        return "\n".join(summary)
    
    def plot_equity_curve(self, title="Equity Curve"):
        """
        Plot the equity curve
        
        Parameters:
        -----------
        title : str
            Plot title
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive plotly figure
        """
        if self.equity_curve is None or len(self.equity_curve) == 0:
            logger.warning("No equity curve data available for plotting")
            return None
        
        try:
            # Create the figure
            fig = go.Figure()
            
            # Add equity curve
            fig.add_trace(go.Scatter(
                x=self.equity_curve.index,
                y=self.equity_curve.values,
                mode='lines',
                name='Equity',
                line=dict(color='green', width=2)
            ))
            
            # Calculate drawdown
            running_max = self.equity_curve.cummax()
            drawdown = self.equity_curve - running_max
            
            # Add drawdown
            fig.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                mode='lines',
                name='Drawdown',
                line=dict(color='red', width=1)
            ))
            
            # Add title and labels
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Equity",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white"
            )
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting equity curve: {str(e)}")
            return None
    
    def plot_trade_distribution(self, title="Trade Distribution"):
        """
        Plot the distribution of trade profits
        
        Parameters:
        -----------
        title : str
            Plot title
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive plotly figure
        """
        if self.trades_df is None or len(self.trades_df) == 0:
            logger.warning("No trade data available for plotting")
            return None
        
        try:
            # Create the figure
            fig = go.Figure()
            
            # Add histogram of profits
            fig.add_trace(go.Histogram(
                x=self.trades_df['profit'],
                name='Profit Distribution',
                nbinsx=20,
                marker_color='blue',
                opacity=0.7
            ))
            
            # Add vertical line at zero
            fig.add_vline(
                x=0,
                line_width=2,
                line_dash="dash",
                line_color="red"
            )
            
            # Add title and labels
            fig.update_layout(
                title=title,
                xaxis_title="Profit/Loss",
                yaxis_title="Count",
                template="plotly_white"
            )
            
            return fig
        
        except Exception as e:
            logger.error(f"Error plotting trade distribution: {str(e)}")
            return None
    
    def create_performance_dashboard(self, title="Strategy Performance Dashboard"):
        """
        Create a comprehensive performance dashboard
        
        Parameters:
        -----------
        title : str
            Dashboard title
            
        Returns:
        --------
        plotly.graph_objects.Figure
            Interactive plotly figure with multiple subplots
        """
        if self.trades_df is None or len(self.trades_df) == 0:
            logger.warning("No trade data available for dashboard creation")
            return None
        
        try:
            # Create subplot figure
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    "Equity Curve", "Drawdown",
                    "Trade Profit Distribution", "Win/Loss Ratio",
                    "Trade Results by Direction", "Profit by Timeframe"
                ),
                vertical_spacing=0.1,
                specs=[
                    [{"colspan": 2}, None],
                    [{"type": "xy"}, {"type": "domain"}],
                    [{"type": "xy"}, {"type": "xy"}]
                ]
            )
            
            # Add equity curve if available
            if self.equity_curve is not None and len(self.equity_curve) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=self.equity_curve.index, 
                        y=self.equity_curve.values,
                        mode='lines',
                        name='Equity',
                        line=dict(color='green', width=2)
                    ),
                    row=1, col=1
                )
                
                # Calculate drawdown
                running_max = self.equity_curve.cummax()
                drawdown = (self.equity_curve - running_max) / running_max * 100
                
                # Add drawdown line to same subplot (secondary y-axis)
                fig.add_trace(
                    go.Scatter(
                        x=drawdown.index, 
                        y=drawdown.values,
                        mode='lines',
                        name='Drawdown %',
                        line=dict(color='red', width=1),
                        yaxis="y2"
                    ),
                    row=1, col=1
                )
                
                # Configure secondary y-axis for drawdown
                fig.update_layout(
                    yaxis2=dict(
                        title="Drawdown %",
                        titlefont=dict(color="red"),
                        tickfont=dict(color="red"),
                        anchor="x",
                        overlaying="y",
                        side="right"
                    )
                )
            
            # Add trade profit distribution histogram
            fig.add_trace(
                go.Histogram(
                    x=self.trades_df['profit'],
                    name='Profit Distribution',
                    nbinsx=20,
                    marker_color='blue',
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # Add win/loss pie chart
            win_count = self.metrics.get('winning_trades', 0)
            loss_count = self.metrics.get('losing_trades', 0)
            
            fig.add_trace(
                go.Pie(
                    labels=['Winning Trades', 'Losing Trades'],
                    values=[win_count, loss_count],
                    name='Win/Loss Ratio',
                    marker_colors=['green', 'red'],
                    textinfo='percent+value',
                    hole=0.4
                ),
                row=2, col=2
            )
            
            # Add direction breakdown if available
            if 'direction' in self.trades_df.columns:
                directions = self.trades_df['direction'].unique()
                direction_profits = [self.trades_df[self.trades_df['direction'] == d]['profit'].sum() for d in directions]
                
                fig.add_trace(
                    go.Bar(
                        x=directions,
                        y=direction_profits,
                        name='Profit by Direction',
                        marker_color=['green' if p > 0 else 'red' for p in direction_profits]
                    ),
                    row=3, col=1
                )
            
            # Add timeframe breakdown if available
            if 'timeframe' in self.trades_df.columns:
                timeframes = self.trades_df['timeframe'].unique()
                tf_profits = [self.trades_df[self.trades_df['timeframe'] == tf]['profit'].sum() for tf in timeframes]
                
                fig.add_trace(
                    go.Bar(
                        x=timeframes,
                        y=tf_profits,
                        name='Profit by Timeframe',
                        marker_color=['green' if p > 0 else 'red' for p in tf_profits]
                    ),
                    row=3, col=2
                )
            
            # Add vertical line at zero for profit distribution
            fig.add_vline(
                x=0,
                line_width=2,
                line_dash="dash",
                line_color="red",
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title=title,
                showlegend=False,
                template="plotly_white",
                height=1000
            )
            
            # Update axis labels
            fig.update_xaxes(title_text="Date", row=1, col=1)
            fig.update_yaxes(title_text="Equity", row=1, col=1)
            
            fig.update_xaxes(title_text="Profit/Loss", row=2, col=1)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            
            fig.update_xaxes(title_text="Direction", row=3, col=1)
            fig.update_yaxes(title_text="Profit", row=3, col=1)
            
            fig.update_xaxes(title_text="Timeframe", row=3, col=2)
            fig.update_yaxes(title_text="Profit", row=3, col=2)
            
            return fig
        
        except Exception as e:
            logger.error(f"Error creating performance dashboard: {str(e)}")
            return None

def calculate_trade_metrics(entries, exits, initial_balance=10000.0):
    """
    Calculate trade metrics from entry and exit signals
    
    Parameters:
    -----------
    entries : pandas.DataFrame
        DataFrame with entry signals
    exits : pandas.DataFrame
        DataFrame with exit signals
    initial_balance : float
        Initial account balance
        
    Returns:
    --------
    tuple
        (trades_df, equity_curve)
    """
    if entries is None or exits is None or len(entries) == 0 or len(exits) == 0:
        logger.warning("No entry or exit signals provided for trade metric calculation")
        return pd.DataFrame(), pd.Series()
    
    try:
        # Ensure entries and exits are sorted by date
        entries = entries.sort_index()
        exits = exits.sort_index()
        
        # Create trade list
        trades = []
        equity = initial_balance
        equity_points = [(entries.index[0], equity)]
        
        for i, entry_row in entries.iterrows():
            # Find the next exit after this entry
            exit_after = exits[exits.index > i]
            if len(exit_after) == 0:
                continue
                
            exit_idx = exit_after.index[0]
            exit_row = exits.loc[exit_idx]
            
            # Calculate profit/loss
            if entry_row.get('direction', 'long') == 'long':
                profit = exit_row.get('price', 0) - entry_row.get('price', 0)
            else:
                profit = entry_row.get('price', 0) - exit_row.get('price', 0)
            
            # Apply position size if available
            if 'size' in entry_row:
                profit *= entry_row['size']
            
            # Calculate trade metrics
            trade = {
                'entry_time': i,
                'exit_time': exit_idx,
                'entry_price': entry_row.get('price', 0),
                'exit_price': exit_row.get('price', 0),
                'profit': profit,
                'duration': (exit_idx - i).total_seconds() / 3600  # Duration in hours
            }
            
            # Add direction if available
            if 'direction' in entry_row:
                trade['direction'] = entry_row['direction']
            
            # Add timeframe if available
            if 'timeframe' in entry_row:
                trade['timeframe'] = entry_row['timeframe']
            
            # Add risk if available
            if 'stop_price' in entry_row:
                if entry_row.get('direction', 'long') == 'long':
                    risk = entry_row['price'] - entry_row['stop_price']
                else:
                    risk = entry_row['stop_price'] - entry_row['price']
                
                # Apply position size if available
                if 'size' in entry_row:
                    risk *= entry_row['size']
                
                trade['risk'] = risk
            
            # Update equity
            equity += profit
            equity_points.append((exit_idx, equity))
            
            trades.append(trade)
        
        # Create trades DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Create equity curve
        equity_series = pd.Series([p[1] for p in equity_points], index=[p[0] for p in equity_points])
        
        return trades_df, equity_series
    
    except Exception as e:
        logger.error(f"Error calculating trade metrics: {str(e)}")
        return pd.DataFrame(), pd.Series() 