"""
Performance dashboard for visualizing backtest results.

This module contains functions for creating interactive visualizations of backtest results,
including equity curves, trade analysis, and strategy performance metrics.
"""

import pandas as pd
import numpy as np
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

logger = logging.getLogger(__name__)

def create_performance_dashboard(trades_df, timeframe_data, metrics, equity_curve, params=None):
    """
    Create a comprehensive performance dashboard with multiple visualizations.
    
    Args:
        trades_df: DataFrame with trade results
        timeframe_data: TimeframeData instance
        metrics: Dictionary of performance metrics
        equity_curve: DataFrame with equity curve data
        params: Strategy parameters
        
    Returns:
        plotly.graph_objects.Figure: Interactive dashboard figure
    """
    if trades_df.empty or equity_curve.empty:
        logger.warning("No trade data available for dashboard")
        return go.Figure()
    
    # Create figure with subplots
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"colspan": 2}, None],
            [{}, {}],
            [{}, {}],
            [{}, {}]
        ],
        subplot_titles=(
            "Equity Curve with Drawdown",
            "Performance by Timeframe", "Monthly Returns",
            "Extension Map", "Trade Results by Direction",
            "Profit Distribution", "Timeframe Progression"
        ),
        vertical_spacing=0.10
    )
    
    # 1. Add equity curve with drawdown overlay
    add_equity_curve_plot(fig, equity_curve, row=1, col=1)
    
    # 2. Add performance by timeframe
    if 'trades_by_timeframe' in metrics:
        add_performance_by_timeframe_plot(fig, metrics, row=2, col=1)
    
    # 3. Add monthly returns
    if 'monthly_returns' in metrics:
        add_monthly_returns_plot(fig, metrics, row=2, col=2)
    
    # 4. Add extension map visualization (only if available)
    extension_map = create_extension_map(timeframe_data)
    if extension_map is not None:
        fig.add_trace(extension_map, row=3, col=1)
    
    # 5. Add trade results by direction (Long/Short)
    add_trade_results_by_direction_plot(fig, trades_df, row=3, col=2)
    
    # 6. Add profit distribution
    add_profit_distribution_plot(fig, trades_df, row=4, col=1)
    
    # 7. Add timeframe progression visualization
    if 'is_progression' in trades_df.columns and 'parent_timeframe' in trades_df.columns:
        add_timeframe_progression_plot(fig, trades_df, row=4, col=2)
    
    # Update layout
    fig.update_layout(
        height=1200,
        width=1000,
        title_text="MT 9 EMA Strategy Performance Dashboard",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )
    
    return fig

def add_equity_curve_plot(fig, equity_curve, row=1, col=1):
    """
    Add equity curve with drawdown overlay to a figure.
    
    Args:
        fig: Plotly figure to add to
        equity_curve: Equity curve DataFrame
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if equity_curve.empty or 'balance' not in equity_curve.columns:
        return
    
    # Add equity curve
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve['balance'],
            mode='lines',
            name='Equity',
            line=dict(color='green', width=2)
        ),
        row=row, col=col
    )
    
    # Add drawdown overlay on secondary y-axis
    if 'drawdown_pct' in equity_curve.columns:
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['drawdown_pct'] * 100,  # Convert to percentage
                mode='lines',
                name='Drawdown %',
                yaxis="y2",
                line=dict(color='red', width=1.5)
            ),
            row=row, col=col
        )
        
        # Setup secondary y-axis
        fig.update_layout(
            yaxis2=dict(
                title="Drawdown %",
                overlaying="y",
                side="right",
                showgrid=False,
                range=[0, max(equity_curve['drawdown_pct'] * 100) * 1.5]  # Set range with some margin
            )
        )
    
    # Update axes
    fig.update_xaxes(title_text="Date", row=row, col=col)
    fig.update_yaxes(title_text="Account Balance ($)", row=row, col=col)

def add_performance_by_timeframe_plot(fig, metrics, row=2, col=1):
    """
    Add performance by timeframe plot to a figure.
    
    Args:
        fig: Plotly figure to add to
        metrics: Dictionary of performance metrics
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if 'trades_by_timeframe' not in metrics:
        return
    
    # Extract data
    timeframes = list(metrics['trades_by_timeframe'].keys())
    trade_counts = list(metrics['trades_by_timeframe'].values())
    win_rates = [metrics['win_rate_by_timeframe'].get(tf, 0) * 100 for tf in timeframes]  # Convert to percentage
    profits = [metrics['profit_by_timeframe'].get(tf, 0) for tf in timeframes]
    
    # Create subplot with secondary y-axis
    fig.add_trace(
        go.Bar(
            x=timeframes,
            y=trade_counts,
            name='Trade Count',
            marker_color='blue',
            opacity=0.7
        ),
        row=row, col=col
    )
    
    fig.add_trace(
        go.Scatter(
            x=timeframes,
            y=win_rates,
            mode='lines+markers',
            name='Win Rate %',
            yaxis="y3",
            marker=dict(color='green', size=8),
            line=dict(color='green', width=2)
        ),
        row=row, col=col
    )
    
    # Setup secondary y-axis
    fig.update_layout(
        yaxis3=dict(
            title="Win Rate %",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, 100]
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text="Timeframe", row=row, col=col)
    fig.update_yaxes(title_text="Trade Count", row=row, col=col)

def add_monthly_returns_plot(fig, metrics, row=2, col=2):
    """
    Add monthly returns plot to a figure.
    
    Args:
        fig: Plotly figure to add to
        metrics: Dictionary of performance metrics
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if 'monthly_returns' not in metrics:
        return
    
    # Extract data
    monthly_returns = metrics['monthly_returns']
    months = list(monthly_returns.keys())
    returns = list(monthly_returns.values())
    
    # Format month labels
    month_labels = [str(m)[:7] if hasattr(m, 'strftime') else str(m) for m in months]
    
    # Create color map for positive/negative returns
    colors = ['green' if r >= 0 else 'red' for r in returns]
    
    # Add monthly returns bar chart
    fig.add_trace(
        go.Bar(
            x=month_labels,
            y=returns,
            name='Monthly Returns',
            marker_color=colors
        ),
        row=row, col=col
    )
    
    # Add zero line
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        y0=0,
        y1=0,
        xref="paper",
        yref="y",
        line=dict(color="black", width=1, dash="dash"),
        row=row, col=col
    )
    
    # Update axes
    fig.update_xaxes(title_text="Month", row=row, col=col)
    fig.update_yaxes(title_text="Profit/Loss ($)", row=row, col=col)

def create_extension_map(timeframe_data):
    """
    Create a heatmap visualization of extensions across timeframes.
    
    Args:
        timeframe_data: TimeframeData instance
        
    Returns:
        plotly.graph_objects.Heatmap or None
    """
    # This is a placeholder. In practice, you'd need to extract extension data
    # from all timeframes and create a composite visualization.
    # For now, just return None since we don't have the extension map data
    return None

def add_trade_results_by_direction_plot(fig, trades_df, row=3, col=2):
    """
    Add trade results by direction (Long/Short) to a figure.
    
    Args:
        fig: Plotly figure to add to
        trades_df: DataFrame with trade results
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if trades_df.empty or 'type' not in trades_df.columns:
        return
    
    # Group by type and win/loss
    type_win_counts = trades_df.groupby(['type', 'win']).size().unstack(fill_value=0)
    
    # If the DataFrame doesn't have the expected structure, try to fix it
    if True not in type_win_counts.columns:
        type_win_counts[True] = 0
    if False not in type_win_counts.columns:
        type_win_counts[False] = 0
    
    # Extract data
    trade_types = type_win_counts.index.tolist()
    wins = type_win_counts[True].tolist()
    losses = type_win_counts[False].tolist()
    
    # Add grouped bar chart
    fig.add_trace(
        go.Bar(
            x=trade_types,
            y=wins,
            name='Wins',
            marker_color='green'
        ),
        row=row, col=col
    )
    
    fig.add_trace(
        go.Bar(
            x=trade_types,
            y=losses,
            name='Losses',
            marker_color='red'
        ),
        row=row, col=col
    )
    
    # Update layout for grouped bars
    fig.update_layout(barmode='group')
    
    # Add win rate annotation for each type
    for i, t in enumerate(trade_types):
        total = wins[i] + losses[i]
        win_rate = wins[i] / total * 100 if total > 0 else 0
        
        fig.add_annotation(
            x=t,
            y=max(wins[i], losses[i]) + 1,
            text=f"{win_rate:.1f}%",
            showarrow=False,
            row=row, col=col
        )
    
    # Update axes
    fig.update_xaxes(title_text="Trade Direction", row=row, col=col)
    fig.update_yaxes(title_text="Count", row=row, col=col)

def add_profit_distribution_plot(fig, trades_df, row=4, col=1):
    """
    Add profit distribution histogram to a figure.
    
    Args:
        fig: Plotly figure to add to
        trades_df: DataFrame with trade results
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if trades_df.empty or 'profit' not in trades_df.columns:
        return
    
    # Create profit histogram
    fig.add_trace(
        go.Histogram(
            x=trades_df['profit'],
            nbinsx=20,
            name='Profit Distribution',
            marker_color='blue',
            opacity=0.7
        ),
        row=row, col=col
    )
    
    # Add zero line
    fig.add_shape(
        type="line",
        x0=0,
        x1=0,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="black", width=1, dash="dash"),
        row=row, col=col
    )
    
    # Update axes
    fig.update_xaxes(title_text="Profit/Loss ($)", row=row, col=col)
    fig.update_yaxes(title_text="Count", row=row, col=col)

def add_timeframe_progression_plot(fig, trades_df, row=4, col=2):
    """
    Add timeframe progression visualization to a figure.
    
    Args:
        fig: Plotly figure to add to
        trades_df: DataFrame with trade results
        row: Row position in subplot grid
        col: Column position in subplot grid
    """
    if trades_df.empty or 'is_progression' not in trades_df.columns or 'parent_timeframe' not in trades_df.columns:
        return
    
    # Filter to progression trades only
    progression_trades = trades_df[trades_df['is_progression'] == True]
    if progression_trades.empty:
        return
    
    # Group by parent and current timeframe
    progression_counts = progression_trades.groupby(['parent_timeframe', 'timeframe']).size().reset_index(name='count')
    
    # Create Sankey diagram data structure
    # This is a simple version - for a real implementation, you would need to create
    # source/target indices and values for a Sankey diagram
    
    # For now, use a simpler bar chart
    fig.add_trace(
        go.Bar(
            x=progression_counts['parent_timeframe'] + ' → ' + progression_counts['timeframe'],
            y=progression_counts['count'],
            name='Progression Paths',
            marker_color='purple',
            opacity=0.7
        ),
        row=row, col=col
    )
    
    # Update axes
    fig.update_xaxes(title_text="Timeframe Progression", row=row, col=col)
    fig.update_yaxes(title_text="Count", row=row, col=col)

def create_trade_timeline(trades_df, timeframe_data):
    """
    Create a timeline visualization of trades across timeframes.
    
    Args:
        trades_df: DataFrame with trade results
        timeframe_data: TimeframeData instance
        
    Returns:
        plotly.graph_objects.Figure: Trade timeline figure
    """
    if trades_df.empty or 'entry_time' not in trades_df.columns:
        return go.Figure()
    
    # Create figure
    fig = go.Figure()
    
    # Extract unique timeframes
    timeframes = sorted(trades_df['timeframe'].unique()) if 'timeframe' in trades_df.columns else ['All']
    
    # Assign y-position for each timeframe
    timeframe_positions = {tf: i for i, tf in enumerate(timeframes)}
    
    # Add traces for each trade type
    colors = {'LONG': 'green', 'SHORT': 'red'}
    
    for trade_type, color in colors.items():
        type_trades = trades_df[trades_df['type'] == trade_type] if 'type' in trades_df.columns else pd.DataFrame()
        
        if not type_trades.empty:
            # Prepare hover text
            hover_texts = []
            for _, trade in type_trades.iterrows():
                hover_text = f"Type: {trade['type']}<br>"
                hover_text += f"Timeframe: {trade['timeframe']}<br>"
                hover_text += f"Entry: {trade['entry_time']}<br>"
                hover_text += f"Exit: {trade['exit_time']}<br>"
                hover_text += f"Entry Price: ${trade['entry_price']:.2f}<br>"
                hover_text += f"Exit Price: ${trade['exit_price']:.2f}<br>"
                hover_text += f"Profit: ${trade['profit']:.2f}<br>"
                
                # Add additional info if available
                if 'is_progression' in trade and trade['is_progression']:
                    hover_text += f"Progression from: {trade['parent_timeframe']}<br>"
                
                if 'conflict_type' in trade and trade['conflict_type'] != "None":
                    hover_text += f"Conflict: {trade['conflict_type']}<br>"
                
                hover_texts.append(hover_text)
            
            # Calculate marker size based on profit
            if 'profit' in type_trades.columns:
                # Normalize profit to reasonable marker sizes (5-20)
                max_abs_profit = max(abs(type_trades['profit'].max()), abs(type_trades['profit'].min()))
                if max_abs_profit > 0:
                    marker_sizes = 10 + (type_trades['profit'] / max_abs_profit) * 10
                else:
                    marker_sizes = 10
            else:
                marker_sizes = 10
            
            # Get y-positions based on timeframe
            if 'timeframe' in type_trades.columns:
                y_positions = [timeframe_positions[tf] for tf in type_trades['timeframe']]
            else:
                y_positions = [0] * len(type_trades)
            
            # Add scatter plot for this trade type
            fig.add_trace(
                go.Scatter(
                    x=type_trades['entry_time'],
                    y=y_positions,
                    mode='markers',
                    marker=dict(
                        size=marker_sizes,
                        color=color,
                        opacity=0.7,
                        line=dict(width=1, color='black')
                    ),
                    name=trade_type,
                    text=hover_texts,
                    hoverinfo='text'
                )
            )
    
    # Add lines to connect related trades (progressions)
    if 'is_progression' in trades_df.columns and 'parent_timeframe' in trades_df.columns:
        progression_trades = trades_df[trades_df['is_progression'] == True]
        
        for _, trade in progression_trades.iterrows():
            # Find the parent trade
            parent_trades = trades_df[
                (trades_df['timeframe'] == trade['parent_timeframe']) & 
                (trades_df['exit_time'] <= trade['entry_time'])
            ]
            
            if not parent_trades.empty:
                # Get the most recent parent trade
                parent_trade = parent_trades.sort_values('exit_time').iloc[-1]
                
                # Add a line connecting parent to child
                fig.add_trace(
                    go.Scatter(
                        x=[parent_trade['exit_time'], trade['entry_time']],
                        y=[timeframe_positions[parent_trade['timeframe']], timeframe_positions[trade['timeframe']]],
                        mode='lines',
                        line=dict(color='gray', width=1, dash='dot'),
                        showlegend=False
                    )
                )
    
    # Update layout
    fig.update_layout(
        title="Trade Timeline Across Timeframes",
        xaxis_title="Date",
        yaxis=dict(
            title="Timeframe",
            tickmode='array',
            tickvals=list(timeframe_positions.values()),
            ticktext=list(timeframe_positions.keys())
        ),
        height=600,
        template="plotly_white"
    )
    
    return fig

def create_extension_signal_map(timeframe_data):
    """
    Create a visualization of extensions and signals across timeframes.
    
    Args:
        timeframe_data: TimeframeData instance
        
    Returns:
        plotly.graph_objects.Figure: Extension signal map figure
    """
    # This is a placeholder since implementing this would require specific 
    # data structures from timeframe_data that aren't defined yet
    fig = go.Figure()
    
    fig.update_layout(
        title="Extension Signal Map (Placeholder)",
        xaxis_title="Date",
        yaxis_title="Timeframe",
        height=600,
        template="plotly_white"
    )
    
    # Add a note about implementation
    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text="Extension Signal Map visualization requires timeframe data",
        showarrow=False,
        font=dict(size=14)
    )
    
    return fig 