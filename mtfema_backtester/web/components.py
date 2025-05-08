#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI Components for the MTFEMA Backtester web interface

This module provides specialized UI components for the web interface.

Timestamp: 2025-05-06 PST
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def performance_metrics_card(metrics):
    """
    Display a card with performance metrics
    
    Parameters:
    -----------
    metrics : dict
        Dictionary of performance metrics
    """
    st.subheader("Performance Metrics")
    
    metrics_container = st.container()
    with metrics_container:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Return",
                value=f"{metrics.get('total_return', 0.0):.2f}%",
                delta=f"{metrics.get('benchmark_diff', 0.0):.2f}%"
            )
            
            st.metric(
                label="Win Rate",
                value=f"{metrics.get('win_rate', 0.0):.2f}%"
            )
        
        with col2:
            st.metric(
                label="Profit Factor",
                value=f"{metrics.get('profit_factor', 0.0):.2f}"
            )
            
            st.metric(
                label="Max Drawdown",
                value=f"{metrics.get('max_drawdown', 0.0):.2f}%",
                delta=f"{metrics.get('recovery_time', 0)} days",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="Sharpe Ratio",
                value=f"{metrics.get('sharpe_ratio', 0.0):.2f}"
            )
            
            st.metric(
                label="Trades",
                value=f"{metrics.get('total_trades', 0)}"
            )
        
        with col4:
            st.metric(
                label="Avg. Holding Time",
                value=f"{metrics.get('avg_hold_time', 0)} days"
            )
            
            st.metric(
                label="Expectancy",
                value=f"${metrics.get('expectancy', 0.0):.2f}"
            )

def equity_curve(data):
    """
    Display an equity curve chart
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with equity curve data
    """
    st.subheader("Equity Curve")
    
    fig = go.Figure()
    
    # Add equity curve line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data['equity'],
            mode='lines',
            name='Strategy',
            line=dict(color='#2563EB', width=2)
        )
    )
    
    # Add benchmark if available
    if 'benchmark' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['benchmark'],
                mode='lines',
                name='Benchmark',
                line=dict(color='#6B7280', width=1.5, dash='dash')
            )
        )
    
    # Add drawdown overlay if available
    if 'drawdown' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['drawdown'],
                mode='lines',
                name='Drawdown',
                line=dict(color='#DC2626', width=1),
                visible='legendonly'  # Hide by default, toggleable in legend
            )
        )
    
    # Update layout
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)'
        ),
        yaxis=dict(
            title="Equity ($)",
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)'
        ),
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def strategy_parameters_form():
    """
    Display a form for strategy parameters
    
    Returns:
    --------
    dict
        Dictionary of strategy parameters
    """
    with st.form("strategy_parameters"):
        st.subheader("Strategy Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ema_period = st.number_input(
                "EMA Period", 
                min_value=1, 
                max_value=50, 
                value=9,
                help="Period for the EMA calculation"
            )
            
            use_atr = st.checkbox(
                "Use ATR for Stop Loss", 
                value=True,
                help="Use Average True Range for stop loss calculation"
            )
            
            atr_multiplier = st.number_input(
                "ATR Multiplier", 
                min_value=0.5, 
                max_value=5.0, 
                value=2.0,
                step=0.1,
                disabled=not use_atr,
                help="Multiplier for ATR to determine stop loss distance"
            )
        
        with col2:
            risk_per_trade = st.number_input(
                "Risk Per Trade (%)", 
                min_value=0.1, 
                max_value=10.0, 
                value=1.0,
                step=0.1,
                help="Percentage of account to risk per trade"
            )
            
            use_extension_filter = st.checkbox(
                "Filter Entries by Extension", 
                value=True,
                help="Only enter trades when price is extended from EMA"
            )
            
            extension_threshold = st.number_input(
                "Extension Threshold (%)", 
                min_value=0.1, 
                max_value=5.0, 
                value=0.5,
                step=0.1,
                disabled=not use_extension_filter,
                help="Minimum extension percentage required for entry"
            )
        
        submitted = st.form_submit_button("Apply Parameters")
        
        parameters = {
            "ema_period": ema_period,
            "use_atr": use_atr,
            "atr_multiplier": atr_multiplier,
            "risk_per_trade": risk_per_trade,
            "use_extension_filter": use_extension_filter,
            "extension_threshold": extension_threshold,
            "submitted": submitted
        }
        
        return parameters

def timeframe_selector():
    """
    Display a timeframe selector with hierarchical checkboxes
    
    Returns:
    --------
    list
        List of selected timeframes
    """
    st.subheader("Timeframe Selection")
    
    # Group timeframes into categories
    intraday = st.checkbox("Intraday", value=True)
    intraday_tf = st.multiselect(
        "Select Intraday Timeframes",
        options=["1m", "5m", "15m", "30m", "1h", "4h"],
        default=["15m", "1h"],
        disabled=not intraday
    )
    
    daily = st.checkbox("Daily", value=True)
    daily_tf = st.multiselect(
        "Select Daily Timeframes",
        options=["1d"],
        default=["1d"],
        disabled=not daily
    )
    
    weekly = st.checkbox("Weekly", value=False)
    weekly_tf = st.multiselect(
        "Select Weekly Timeframes",
        options=["1w"],
        default=[],
        disabled=not weekly
    )
    
    # Combine selected timeframes
    selected_timeframes = []
    if intraday:
        selected_timeframes.extend(intraday_tf)
    if daily:
        selected_timeframes.extend(daily_tf)
    if weekly:
        selected_timeframes.extend(weekly_tf)
    
    return selected_timeframes

def trades_table(trades_df):
    """
    Display a table of trades with formatting
    
    Parameters:
    -----------
    trades_df : pandas.DataFrame
        DataFrame containing trade information
    """
    st.subheader("Trades")
    
    # Ensure trades_df has required columns
    required_columns = ['Entry Time', 'Exit Time', 'Symbol', 'Direction', 'Entry Price', 
                        'Exit Price', 'Profit/Loss', 'Return (%)', 'Duration']
    
    if not all(col in trades_df.columns for col in required_columns):
        st.error("Trades data is missing required columns.")
        return
    
    # Format the trades DataFrame for display
    display_df = trades_df.copy()
    
    # Add color formatting based on return
    def color_returns(val):
        color = '#10B981' if val > 0 else '#EF4444' if val < 0 else '#6B7280'
        return f'color: {color}; font-weight: bold'
    
    # Apply the formatting
    styled_df = display_df.style.applymap(
        color_returns, 
        subset=['Profit/Loss', 'Return (%)']
    )
    
    # Display the styled table
    st.dataframe(styled_df, use_container_width=True)

def symbol_search():
    """
    Display a symbol search box with suggestions
    
    Returns:
    --------
    str
        Selected symbol
    """
    st.subheader("Symbol Selection")
    
    # Sample symbols for suggestions
    popular_symbols = {
        "Indices": ["^GSPC (S&P 500)", "^DJI (Dow Jones)", "^IXIC (Nasdaq)", "^RUT (Russell 2000)"],
        "Futures": ["ES=F (S&P 500)", "NQ=F (Nasdaq 100)", "YM=F (Dow Jones)", "CL=F (Crude Oil)", "GC=F (Gold)"],
        "Stocks": ["AAPL (Apple)", "MSFT (Microsoft)", "AMZN (Amazon)", "GOOGL (Google)", "META (Meta)"],
        "Forex": ["EURUSD=X (EUR/USD)", "GBPUSD=X (GBP/USD)", "USDJPY=X (USD/JPY)"]
    }
    
    # User can select a category then a symbol
    category = st.selectbox("Category", list(popular_symbols.keys()))
    
    # Extract symbols without the descriptions for the selectbox
    symbol_options = popular_symbols[category]
    symbol_selection = st.selectbox("Select Symbol", symbol_options)
    
    # Extract just the symbol part (before the space)
    selected_symbol = symbol_selection.split(" ")[0]
    
    # Allow manual entry
    custom_symbol = st.text_input("Or enter custom symbol:", "")
    
    # Return either the selected symbol or the custom one if provided
    return custom_symbol if custom_symbol else selected_symbol 