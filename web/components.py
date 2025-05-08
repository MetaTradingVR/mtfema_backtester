import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

def create_sidebar():
    """Creates the sidebar with strategy controls and information"""
    with st.sidebar:
        st.header("Strategy Controls")

        st.subheader("General Settings")
        initial_capital = st.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=10000000,
            value=st.session_state.initial_capital,
            step=1000,
            help="Starting capital for the backtest"
        )
        st.session_state.initial_capital = initial_capital

        st.subheader("Risk Management")
        risk_percentage = st.slider(
            "Risk per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=st.session_state.risk_percentage,
            step=0.1,
            help="Maximum percentage of capital to risk on each trade"
        )
        st.session_state.risk_percentage = risk_percentage

        use_atr_stops = st.checkbox(
            "Use ATR-based Stops",
            value=st.session_state.use_atr_stops,
            help="Use Average True Range for stop loss calculation"
        )
        st.session_state.use_atr_stops = use_atr_stops

        if use_atr_stops:
            atr_multiplier = st.slider(
                "ATR Multiplier",
                min_value=0.5,
                max_value=5.0,
                value=st.session_state.atr_multiplier,
                step=0.1,
                help="Multiplier applied to ATR for stop loss calculation"
            )
            st.session_state.atr_multiplier = atr_multiplier

        st.markdown("---")
        
        st.subheader("About")
        st.markdown("""
        The **Multi-Timeframe 9 EMA Extension Strategy** is a trading system that identifies opportunities when price extends from the 9 EMA across multiple timeframes.
        
        Key aspects:
        - Extension detection from 9 EMA
        - Multi-timeframe confluence
        - Progressive target approach
        - Risk-adjusted position sizing
        """)
        
        st.markdown("---")
        
        # Version info
        st.markdown("<small>Version 1.0.0 | © 2025</small>", unsafe_allow_html=True)


def create_parameter_controls():
    """Creates strategy parameter controls"""
    col1, col2 = st.columns(2)
    
    with col1:
        ema_period = st.number_input(
            "EMA Period",
            min_value=3,
            max_value=200,
            value=st.session_state.ema_period,
            step=1,
            help="Period used for the Exponential Moving Average calculation"
        )
        st.session_state.ema_period = ema_period
        
    with col2:
        extension_threshold = st.slider(
            "Extension Threshold",
            min_value=0.1,
            max_value=2.0,
            value=st.session_state.extension_threshold,
            step=0.1,
            help="Minimum price extension from EMA to generate signals (in ATR units)"
        )
        st.session_state.extension_threshold = extension_threshold
    
    st.markdown("---")
    
    # Advanced parameters collapsible section
    with st.expander("Advanced Parameters"):
        col1, col2 = st.columns(2)
        
        with col1:
            lookback_period = st.number_input(
                "Lookback Period",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Number of bars to analyze for pattern detection"
            )
            
            profit_target_multiplier = st.slider(
                "Profit Target Multiplier",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="Risk-to-reward ratio for profit targets"
            )
            
        with col2:
            trailing_stop = st.checkbox(
                "Use Trailing Stop",
                value=True,
                help="Enable trailing stop loss for open positions"
            )
            
            if trailing_stop:
                trailing_activation = st.slider(
                    "Trailing Activation (%)",
                    min_value=0.5,
                    max_value=5.0,
                    value=1.0,
                    step=0.1,
                    help="Profit percentage before trailing stop activates"
                )


def create_symbol_search():
    """Creates a symbol search box with suggestions"""
    
    popular_symbols = ["ES", "NQ", "YM", "CL", "GC", "SI", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "ETHUSD"]
    equity_indices = ["ES", "NQ", "YM", "RTY", "DX", "NIY", "FTSE", "DAX"]
    forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP", "EURJPY"]
    commodities = ["CL", "GC", "SI", "NG", "HG", "ZC", "ZS", "KC", "CT"]
    crypto = ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "ADAUSD", "DOTUSD", "SOLUSD"]
    
    # Create tabs for different symbol categories
    symbol_tabs = st.tabs(["Popular", "Indices", "Forex", "Commodities", "Crypto"])
    
    with symbol_tabs[0]:
        cols = st.columns(3)
        for i, symbol in enumerate(popular_symbols):
            col_idx = i % 3
            if cols[col_idx].button(symbol, key=f"pop_{symbol}"):
                selected_symbol = symbol
                break
        else:
            selected_symbol = st.session_state.selected_symbol
    
    with symbol_tabs[1]:
        cols = st.columns(4)
        for i, symbol in enumerate(equity_indices):
            col_idx = i % 4
            if cols[col_idx].button(symbol, key=f"idx_{symbol}"):
                selected_symbol = symbol
                break
    
    with symbol_tabs[2]:
        cols = st.columns(3)
        for i, symbol in enumerate(forex_pairs):
            col_idx = i % 3
            if cols[col_idx].button(symbol, key=f"fx_{symbol}"):
                selected_symbol = symbol
                break
    
    with symbol_tabs[3]:
        cols = st.columns(3)
        for i, symbol in enumerate(commodities):
            col_idx = i % 3
            if cols[col_idx].button(symbol, key=f"com_{symbol}"):
                selected_symbol = symbol
                break
    
    with symbol_tabs[4]:
        cols = st.columns(3)
        for i, symbol in enumerate(crypto):
            col_idx = i % 3
            if cols[col_idx].button(symbol, key=f"crypto_{symbol}"):
                selected_symbol = symbol
                break
    
    # Allow manual symbol entry
    custom_symbol = st.text_input("Or enter symbol directly:", value=selected_symbol)
    if custom_symbol:
        selected_symbol = custom_symbol.upper()
    
    return selected_symbol


def create_timeframe_selector():
    """Creates a hierarchical timeframe selector"""
    
    all_timeframes = {
        "Intraday": ["1m", "3m", "5m", "15m", "30m"],
        "Hourly": ["1h", "2h", "4h", "8h"],
        "Daily+": ["1d", "1w", "1M"]
    }
    
    st.write("Select Timeframes:")
    
    selected_timeframes = []
    
    # Create an expander for each category
    for category, timeframes in all_timeframes.items():
        with st.expander(category, expanded=True):
            cols = st.columns(len(timeframes))
            for i, tf in enumerate(timeframes):
                if tf in st.session_state.selected_timeframes:
                    default = True
                else:
                    default = False
                
                if cols[i].checkbox(tf, value=default, key=f"tf_{tf}"):
                    selected_timeframes.append(tf)
    
    if not selected_timeframes:
        st.warning("Please select at least one timeframe")
        selected_timeframes = ["1d"]  # Default
    
    # Sort timeframes by duration
    def get_timeframe_minutes(tf):
        if tf.endswith('m'):
            return int(tf[:-1])
        elif tf.endswith('h'):
            return int(tf[:-1]) * 60
        elif tf.endswith('d'):
            return int(tf[:-1]) * 60 * 24
        elif tf.endswith('w'):
            return int(tf[:-1]) * 60 * 24 * 7
        elif tf.endswith('M'):
            return int(tf[:-1]) * 60 * 24 * 30
        return 0
    
    selected_timeframes.sort(key=get_timeframe_minutes)
    
    return selected_timeframes


def display_performance_metrics():
    """Displays key performance metrics in a card-based layout"""
    
    # Generate sample metrics for demonstration
    metrics = {
        "Total Return": f"{random.uniform(10, 50):.2f}%",
        "Win Rate": f"{random.uniform(40, 70):.1f}%",
        "Profit Factor": f"{random.uniform(1.5, 3.0):.2f}",
        "Max Drawdown": f"{random.uniform(5, 20):.2f}%",
        "Sharpe Ratio": f"{random.uniform(0.8, 2.5):.2f}",
        "Total Trades": f"{random.randint(50, 200)}",
        "Avg Profit per Trade": f"${random.uniform(100, 500):.2f}",
        "Avg Hold Time": f"{random.randint(2, 10)} days",
        "Max Consecutive Wins": f"{random.randint(3, 12)}",
    }
    
    # Determine if metrics are positive or negative
    metric_colors = {
        "Total Return": "positive" if float(metrics["Total Return"].strip("%")) > 0 else "negative",
        "Win Rate": "positive" if float(metrics["Win Rate"].strip("%")) >= 50 else "negative",
        "Profit Factor": "positive" if float(metrics["Profit Factor"]) >= 1.5 else "negative",
        "Max Drawdown": "negative",  # Always negative
        "Sharpe Ratio": "positive" if float(metrics["Sharpe Ratio"]) >= 1.0 else "negative",
        "Total Trades": "",  # Neutral
        "Avg Profit per Trade": "positive" if float(metrics["Avg Profit per Trade"].strip("$")) > 0 else "negative",
        "Avg Hold Time": "",  # Neutral
        "Max Consecutive Wins": "",  # Neutral
    }
    
    # Display metrics in a grid
    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    
    for metric, value in metrics.items():
        color_class = metric_colors[metric]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{metric}</div>
            <div class="metric-value {color_class}">{value}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def get_sample_data(n, start=100000, volatility=0.015):
    """Generate sample equity curve data for demonstration"""
    # Start with initial value
    data = [start]
    
    # Generate random walk with upward drift
    for i in range(1, n):
        # Calculate daily return with upward drift
        daily_return = np.random.normal(0.0005, volatility)  # Small positive drift
        
        # Calculate new equity value
        new_value = data[i-1] * (1 + daily_return)
        
        # Add some trading patterns
        if i % 20 == 0:  # Sharp drop every 20 days
            new_value *= 0.98
        
        if i % 50 == 0:  # Strong rally every 50 days
            new_value *= 1.03
            
        data.append(new_value)
    
    return data 