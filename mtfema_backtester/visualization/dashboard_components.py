"""
Dashboard components for the MT 9 EMA Extension Strategy Backtester.

This module contains reusable components for building interactive dashboards.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def create_equity_curve_component(equity_data, title="Equity Curve"):
    """
    Create an equity curve visualization with drawdown overlay.
    
    Args:
        equity_data: DataFrame or list of (datetime, balance) tuples
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    # Convert to DataFrame if it's a list
    if isinstance(equity_data, list):
        equity_df = pd.DataFrame(equity_data, columns=['datetime', 'balance'])
    else:
        equity_df = equity_data.copy()
        
    if equity_df.empty:
        return go.Figure()
    
    # Calculate drawdown
    equity_df['peak'] = equity_df['balance'].cummax()
    equity_df['drawdown'] = (equity_df['peak'] - equity_df['balance']) / equity_df['peak'] * 100
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add equity curve
    fig.add_trace(
        go.Scatter(
            x=equity_df['datetime'],
            y=equity_df['balance'],
            name="Equity",
            line=dict(color='green', width=2)
        ),
        secondary_y=False
    )
    
    # Add drawdown (inverted)
    fig.add_trace(
        go.Scatter(
            x=equity_df['datetime'],
            y=-equity_df['drawdown'],  # Negative to show downward from top
            name="Drawdown",
            fill='tozeroy',
            line=dict(color='red', width=1)
        ),
        secondary_y=True
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Account Balance", secondary_y=False)
    fig.update_yaxes(
        title_text="Drawdown %", 
        secondary_y=True, 
        tickvals=[-10, -20, -30, -40, -50],
        ticktext=['10%', '20%', '30%', '40%', '50%'],
        range=[-50, 0]  # Cap at 50% drawdown for visualization
    )
    
    # Add range slider
    fig.update_layout(
        title=title,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=400
    )
    
    return fig

def create_trade_distribution_component(trades_df, title="Trade P&L Distribution"):
    """
    Create a trade P&L distribution chart.
    
    Args:
        trades_df: DataFrame with trade results
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if trades_df.empty:
        return go.Figure()
    
    # Convert profit_loss column name if needed
    if 'profit_loss' not in trades_df.columns and 'pnl' in trades_df.columns:
        trades_df['profit_loss'] = trades_df['pnl']
    
    # Create bins for histogram
    fig = go.Figure()
    
    # Add histogram for all trades
    fig.add_trace(go.Histogram(
        x=trades_df['profit_loss'],
        name="All Trades",
        opacity=0.7,
        marker_color='blue',
        nbinsx=20
    ))
    
    # Add separate histograms for long and short trades if available
    if 'direction' in trades_df.columns:
        long_trades = trades_df[trades_df['direction'] == 'long']
        short_trades = trades_df[trades_df['direction'] == 'short']
        
        if not long_trades.empty:
            fig.add_trace(go.Histogram(
                x=long_trades['profit_loss'],
                name="Long Trades",
                opacity=0.7,
                marker_color='green',
                nbinsx=20
            ))
            
        if not short_trades.empty:
            fig.add_trace(go.Histogram(
                x=short_trades['profit_loss'],
                name="Short Trades",
                opacity=0.7,
                marker_color='red',
                nbinsx=20
            ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Profit/Loss",
        yaxis_title="Count",
        bargap=0.1,
        bargroupgap=0.2,
        height=400,
        barmode='overlay'
    )
    
    return fig

def create_trade_calendar_component(trades_df, title="Monthly Trade Performance"):
    """
    Create a calendar heatmap of trade performance by month.
    
    Args:
        trades_df: DataFrame with trade results
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if trades_df.empty:
        return go.Figure()
    
    # Ensure datetime column
    datetime_col = None
    for col in ['exit_time', 'entry_time', 'datetime']:
        if col in trades_df.columns:
            datetime_col = col
            break
            
    if not datetime_col:
        return go.Figure()
    
    # Convert profit_loss column name if needed
    if 'profit_loss' not in trades_df.columns and 'pnl' in trades_df.columns:
        trades_df['profit_loss'] = trades_df['pnl']
    
    # Group by year and month
    trades_df['year'] = trades_df[datetime_col].dt.year
    trades_df['month'] = trades_df[datetime_col].dt.month
    
    # Calculate monthly performance
    monthly_performance = trades_df.groupby(['year', 'month']).agg({
        'profit_loss': 'sum', 
        'id': 'count'
    }).reset_index()
    
    monthly_performance.columns = ['year', 'month', 'profit_loss', 'trade_count']
    
    # Create a calendar-style heatmap
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Fill missing months with zeros
    years = monthly_performance['year'].unique()
    full_calendar = []
    
    for year in sorted(years):
        for month in range(1, 13):
            row = monthly_performance[
                (monthly_performance['year'] == year) & 
                (monthly_performance['month'] == month)
            ]
            
            if row.empty:
                full_calendar.append({
                    'year': year,
                    'month': month,
                    'profit_loss': 0,
                    'trade_count': 0
                })
            else:
                full_calendar.append(row.iloc[0].to_dict())
    
    calendar_df = pd.DataFrame(full_calendar)
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=calendar_df['profit_loss'],
        x=calendar_df['month'].apply(lambda m: months[m-1]),
        y=calendar_df['year'],
        colorscale=[
            [0, 'rgb(165,0,38)'],
            [0.45, 'rgb(215,48,39)'],
            [0.5, 'rgb(244,109,67)'],
            [0.55, 'rgb(253,174,97)'],
            [0.6, 'rgb(254,224,144)'],
            [0.65, 'rgb(224,243,248)'],
            [0.7, 'rgb(171,217,233)'],
            [0.75, 'rgb(116,173,209)'],
            [0.8, 'rgb(69,117,180)'],
            [1, 'rgb(49,54,149)']
        ],
        colorbar=dict(title="Profit/Loss"),
        hoverongaps=False,
        hovertemplate='Year: %{y}<br>Month: %{x}<br>P&L: %{z}<extra></extra>'
    ))
    
    # Add trade count as text
    fig.add_trace(go.Heatmap(
        z=calendar_df['trade_count'],
        x=calendar_df['month'].apply(lambda m: months[m-1]),
        y=calendar_df['year'],
        colorscale='Greys',
        showscale=False,
        opacity=0,
        text=calendar_df['trade_count'].apply(lambda c: f"{c} trades" if c > 0 else ""),
        hoverinfo='none',
        texttemplate="%{text}",
        textfont={"size":10}
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Year",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_drawdown_chart(equity_data, title="Drawdown Analysis"):
    """
    Create a standalone drawdown chart with underwater periods.
    
    Args:
        equity_data: DataFrame or list of (datetime, balance) tuples
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    # Convert to DataFrame if it's a list
    if isinstance(equity_data, list):
        equity_df = pd.DataFrame(equity_data, columns=['datetime', 'balance'])
    else:
        equity_df = equity_data.copy()
        
    if equity_df.empty:
        return go.Figure()
    
    # Calculate drawdown series
    equity_df['peak'] = equity_df['balance'].cummax()
    equity_df['drawdown'] = (equity_df['peak'] - equity_df['balance']) / equity_df['peak'] * 100
    
    # Calculate drawdown periods
    in_drawdown = False
    drawdown_periods = []
    current_period = None
    
    for i, row in equity_df.iterrows():
        if row['drawdown'] > 0 and not in_drawdown:
            # Start of drawdown period
            in_drawdown = True
            current_period = {
                'start': row['datetime'],
                'initial_balance': row['peak'],
                'max_drawdown': row['drawdown'],
                'max_drawdown_date': row['datetime']
            }
        elif in_drawdown:
            if row['drawdown'] == 0:
                # End of drawdown period
                in_drawdown = False
                current_period['end'] = row['datetime']
                current_period['duration_days'] = (current_period['end'] - current_period['start']).days
                drawdown_periods.append(current_period)
                current_period = None
            elif row['drawdown'] > current_period['max_drawdown']:
                # Update max drawdown
                current_period['max_drawdown'] = row['drawdown']
                current_period['max_drawdown_date'] = row['datetime']
    
    # Handle if still in drawdown at end of data
    if in_drawdown:
        current_period['end'] = equity_df['datetime'].iloc[-1]
        current_period['duration_days'] = (current_period['end'] - current_period['start']).days
        drawdown_periods.append(current_period)
    
    # Create the drawdown chart
    fig = go.Figure()
    
    # Add drawdown underwater chart
    fig.add_trace(go.Scatter(
        x=equity_df['datetime'],
        y=-equity_df['drawdown'],
        fill='tozeroy',
        name="Drawdown",
        line=dict(color='rgba(220,20,60,0.7)', width=1)
    ))
    
    # Annotate major drawdown periods
    major_drawdowns = sorted(drawdown_periods, key=lambda x: x['max_drawdown'], reverse=True)[:5]
    
    for i, dd in enumerate(major_drawdowns):
        if dd['max_drawdown'] > 5:  # Only annotate significant drawdowns
            fig.add_annotation(
                x=dd['max_drawdown_date'],
                y=-dd['max_drawdown'],
                text=f"{dd['max_drawdown']:.1f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="black",
                arrowsize=1,
                arrowwidth=1,
                ax=0,
                ay=-40
            )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Drawdown %",
        yaxis=dict(
            tickvals=[-10, -20, -30, -40, -50],
            ticktext=['10%', '20%', '30%', '40%', '50%'],
            range=[-50, 0]  # Cap at 50% drawdown for visualization
        ),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_timeframe_performance_component(trades_df, title="Performance by Timeframe"):
    """
    Create a chart showing performance metrics by timeframe.
    
    Args:
        trades_df: DataFrame with trade results
        title: Plot title
        
    Returns:
        plotly.graph_objects.Figure
    """
    if trades_df.empty or 'timeframe' not in trades_df.columns:
        return go.Figure()
    
    # Convert profit_loss column name if needed
    if 'profit_loss' not in trades_df.columns and 'pnl' in trades_df.columns:
        trades_df['profit_loss'] = trades_df['pnl']
    
    # Group by timeframe
    tf_performance = trades_df.groupby('timeframe').agg({
        'profit_loss': ['sum', 'count', 'mean'],
        'id': 'count'
    })
    
    tf_performance.columns = ['total_profit', 'win_count', 'avg_profit', 'trade_count']
    tf_performance = tf_performance.reset_index()
    
    # Calculate win rate 
    tf_performance['win_rate'] = (
        trades_df[trades_df['profit_loss'] > 0].groupby('timeframe')['id'].count() / 
        tf_performance['trade_count'] * 100
    ).fillna(0)
    
    # Create bubble chart
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=tf_performance['timeframe'],
        y=tf_performance['total_profit'],
        text=tf_performance.apply(
            lambda row: f"Timeframe: {row['timeframe']}<br>"
                       f"Total P&L: ${row['total_profit']:.2f}<br>"
                       f"Win Rate: {row['win_rate']:.1f}%<br>"
                       f"Trades: {row['trade_count']}",
            axis=1
        ),
        mode='markers',
        marker=dict(
            size=tf_performance['trade_count'] / tf_performance['trade_count'].max() * 50 + 10,
            color=tf_performance['win_rate'],
            colorscale='RdYlGn',
            colorbar=dict(title="Win Rate %"),
            line=dict(width=2, color='DarkSlateGrey')
        ),
        hoverinfo='text'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Timeframe",
        yaxis_title="Total Profit/Loss",
        height=400
    )
    
    return fig

def create_metrics_summary_component(metrics):
    """
    Create a metrics summary card.
    
    Args:
        metrics: Dictionary of performance metrics
        
    Returns:
        HTML div element as string
    """
    if not metrics:
        return "No metrics available"
    
    # Format metrics values
    formatted_metrics = {}
    
    for key, value in metrics.items():
        if isinstance(value, float):
            if key in ['win_rate', 'sharpe_ratio', 'sortino_ratio']:
                formatted_metrics[key] = f"{value:.2f}"
            elif key in ['max_drawdown', 'profit_factor']:
                formatted_metrics[key] = f"{value:.2f}"
            elif 'balance' in key or 'profit' in key or 'loss' in key:
                formatted_metrics[key] = f"${value:.2f}"
            else:
                formatted_metrics[key] = f"{value:.4f}"
        else:
            formatted_metrics[key] = f"{value}"
    
    # Generate HTML
    html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
    """
    
    # Key metrics to display
    key_metrics = [
        ('final_balance', 'Final Balance', 'green'),
        ('total_return_pct', 'Total Return', 'green'),
        ('win_rate', 'Win Rate', 'blue'),
        ('profit_factor', 'Profit Factor', 'blue'),
        ('sharpe_ratio', 'Sharpe Ratio', 'purple'),
        ('max_drawdown', 'Max Drawdown', 'red'),
        ('trade_count', 'Total Trades', 'gray'),
        ('avg_trade', 'Avg Trade P&L', 'gray'),
        ('avg_win', 'Avg Win', 'green'),
        ('avg_loss', 'Avg Loss', 'red')
    ]
    
    for key, label, color in key_metrics:
        value = formatted_metrics.get(key, 'N/A')
        
        html += f"""
        <div style="padding: 12px; background-color: #f8f9fa; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); flex: 1; min-width: 150px; max-width: 250px;">
            <div style="font-size: 14px; color: #6c757d; margin-bottom: 8px;">{label}</div>
            <div style="font-size: 24px; font-weight: bold; color: {color};">{value}</div>
        </div>
        """
    
    html += "</div>"
    return html
