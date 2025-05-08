#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Streamlit web application for the MTFEMA backtester

Provides an interactive interface for running backtests and visualizing results.

Timestamp: 2025-05-06 PST
"""

import os
import sys
import logging
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Import project modules
from mtfema_backtester.data.timeframe_data import TimeframeData
from mtfema_backtester.visualization import (
    plot_extension_map,
    plot_signal_timeline,
    plot_progression_tracker,
    plot_conflict_map
)
from mtfema_backtester.web.components import (
    performance_metrics_card,
    equity_curve,
    strategy_parameters_form,
    timeframe_selector,
    trades_table,
    symbol_search
)
from mtfema_backtester.web.data_fetcher import (
    fetch_yahoo_finance_data,
    calculate_indicators,
    generate_sample_data
)

logger = logging.getLogger(__name__)

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_css():
    """Load custom CSS file"""
    css_path = os.path.join(CURRENT_DIR, "assets", "style.css")
    
    try:
        with open(css_path, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
            logger.info(f"Loaded custom CSS from {css_path}")
    except FileNotFoundError:
        logger.warning(f"Custom CSS file not found at {css_path}")
        # Use inline fallback styles
        st.markdown("""
        <style>
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .stApp { background-color: #f5f7f9; }
        .stSidebar { background-color: #ffffff; }
        h1, h2, h3 { color: #1E3A8A; }
        </style>
        """, unsafe_allow_html=True)

# Set page configuration
def configure_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="MTFEMA Backtester",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_css()

def show_header():
    """Display the application header"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("MT 9 EMA Backtester")
        st.subheader("Multi-Timeframe 9 EMA Extension Strategy Backtester")
    
    with col2:
        st.text("")
        st.text("")
        st.text(f"Version: 1.0.0")
        st.text(f"Last Updated: 2025-05-06")

def sidebar_controls():
    """Create sidebar controls for application settings"""
    with st.sidebar:
        st.header("Settings")
        
        # Symbol selection using the custom component
        selected_symbol = symbol_search()
        
        # Date range selection
        st.subheader("Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=180))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Timeframe selection using the custom component
        selected_timeframes = timeframe_selector()
        
        # Strategy parameters
        st.subheader("Strategy Parameters")
        ema_period = st.number_input("EMA Period", min_value=1, max_value=50, value=9)
        
        # Extension thresholds with custom input for each timeframe
        st.subheader("Extension Thresholds")
        extension_thresholds = {}
        
        for tf in selected_timeframes:
            default_value = 0.5
            if "m" in tf:
                minutes = int(tf.replace("m", ""))
                if minutes <= 5:
                    default_value = 0.3
                elif minutes <= 15:
                    default_value = 0.6
                else:
                    default_value = 0.8
            elif "h" in tf:
                default_value = 1.0
            elif "d" in tf:
                default_value = 2.0
            elif "w" in tf:
                default_value = 3.0
                
            extension_thresholds[tf] = st.number_input(
                f"{tf} Threshold (%)", 
                min_value=0.1, 
                max_value=5.0, 
                value=default_value,
                step=0.1,
                format="%.1f"
            )
        
        # Use sample data option
        use_sample_data = st.checkbox("Use Sample Data", value=True, 
                                     help="Use generated sample data instead of fetching real data")
        
        # Action buttons
        st.subheader("Actions")
        col1, col2 = st.columns(2)
        with col1:
            run_button = st.button("Run Backtest", type="primary", use_container_width=True)
        with col2:
            reset_button = st.button("Reset", use_container_width=True)
        
        return {
            "symbol": selected_symbol,
            "start_date": start_date,
            "end_date": end_date,
            "timeframes": selected_timeframes,
            "ema_period": ema_period,
            "extension_thresholds": extension_thresholds,
            "use_sample_data": use_sample_data,
            "run_backtest": run_button,
            "reset": reset_button
        }

def load_data(settings):
    """Load data based on settings"""
    if settings["run_backtest"]:
        with st.spinner("Loading data..."):
            if settings["use_sample_data"]:
                # Generate sample data
                tf_data = generate_sample_data(settings["timeframes"], periods=200)
                st.success(f"Generated sample data for {', '.join(settings['timeframes'])} timeframes")
            else:
                # Fetch real data
                tf_data = fetch_yahoo_finance_data(
                    settings["symbol"],
                    settings["start_date"],
                    settings["end_date"],
                    settings["timeframes"]
                )
                
                if tf_data is None:
                    st.error(f"Failed to fetch data for {settings['symbol']}")
                    return None
                
                st.success(f"Fetched data for {settings['symbol']}")
            
            # Store in session state
            st.session_state.timeframe_data = tf_data
            
            return tf_data
    
    # Return data from session state if available
    return st.session_state.get("timeframe_data", None)

def main_content(settings):
    """Display the main content area with tabs for different visualizations"""
    # Load data if needed
    timeframe_data = load_data(settings)
    
    # Create tabs for different sections
    tabs = st.tabs(["Dashboard", "Extension Map", "Signal Timeline", "Progression Tracker", "Conflict Map", "Results"])
    
    with tabs[0]:  # Dashboard tab
        st.header("Strategy Dashboard")
        
        if timeframe_data is None:
            st.info("Configure settings in the sidebar and click 'Run Backtest' to see results.")
            
            # Display current settings summary
            st.subheader("Current Settings")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Symbol:** {settings['symbol']}")
                st.write(f"**Date Range:** {settings['start_date']} to {settings['end_date']}")
                st.write(f"**Timeframes:** {', '.join(settings['timeframes'])}")
            
            with col2:
                st.write(f"**EMA Period:** {settings['ema_period']}")
                st.write("**Extension Thresholds:**")
                for tf, threshold in settings['extension_thresholds'].items():
                    st.write(f"  - {tf}: {threshold}%")
        else:
            # Show sample performance metrics
            sample_metrics = {
                "total_return": 24.5,
                "benchmark_diff": 12.3,
                "win_rate": 68.5,
                "profit_factor": 2.4,
                "max_drawdown": 8.7,
                "recovery_time": 14,
                "sharpe_ratio": 1.9,
                "total_trades": 42,
                "avg_hold_time": 5,
                "expectancy": 0.87
            }
            
            performance_metrics_card(sample_metrics)
            
            # Create sample equity curve data
            base_time = datetime.now() - timedelta(days=180)
            timestamps = [base_time + timedelta(days=i) for i in range(180)]
            
            # Generate sample equity curve
            equity = [100.0]
            for i in range(1, 180):
                daily_return = 0.1 * (0.5 - pd.np.random.random())
                equity.append(equity[-1] * (1 + daily_return))
            
            # Generate sample benchmark
            benchmark = [100.0]
            for i in range(1, 180):
                daily_return = 0.08 * (0.5 - pd.np.random.random())
                benchmark.append(benchmark[-1] * (1 + daily_return))
            
            # Generate sample drawdown
            drawdown = [(1 - e / max(equity[:i+1])) * 100 for i, e in enumerate(equity)]
            
            equity_data = pd.DataFrame({
                "equity": equity,
                "benchmark": benchmark,
                "drawdown": drawdown
            }, index=timestamps)
            
            equity_curve(equity_data)
            
            # Show sample trades
            trades_data = []
            for i in range(10):
                entry_time = base_time + timedelta(days=i*15)
                exit_time = entry_time + timedelta(days=3)
                is_long = i % 2 == 0
                
                trade = {
                    "Entry Time": entry_time,
                    "Exit Time": exit_time,
                    "Symbol": settings["symbol"],
                    "Direction": "Long" if is_long else "Short",
                    "Entry Price": 100 + i,
                    "Exit Price": (100 + i) * (1.05 if is_long else 0.95) if i != 5 else (100 + i) * (0.97 if is_long else 1.03),
                    "Profit/Loss": 5 if i != 5 else -3,
                    "Return (%)": 5.0 if i != 5 else -3.0,
                    "Duration": "3 days"
                }
                trades_data.append(trade)
            
            trades_df = pd.DataFrame(trades_data)
            trades_table(trades_df)
    
    if timeframe_data is not None:
        with tabs[1]:  # Extension Map tab
            st.header("Extension Map")
            st.write("The extension map shows extensions across all timeframes, making it easy to identify multi-timeframe confluence.")
            
            try:
                # Create the extension map visualization
                extension_map = plot_extension_map(timeframe_data, lookback=100)
                st.plotly_chart(extension_map, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating extension map visualization: {str(e)}")
        
        with tabs[2]:  # Signal Timeline tab
            st.header("Signal Timeline")
            st.write("The signal timeline displays trading signals chronologically across different timeframes.")
            
            try:
                # Generate sample signals for demonstration
                signals = []
                base_time = datetime.now() - timedelta(days=30)
                
                for i in range(20):
                    direction = "long" if i % 3 != 0 else "short"
                    timeframe = settings["timeframes"][i % len(settings["timeframes"])]
                    confidence = "high" if i % 4 == 0 else "medium" if i % 4 == 1 else "low"
                    
                    signal = {
                        "timeframe": timeframe,
                        "direction": direction,
                        "time": base_time + timedelta(days=i),
                        "price": 100 + i,
                        "confidence": confidence,
                        "target": {
                            "target_timeframe": settings["timeframes"][(i+1) % len(settings["timeframes"])],
                            "target_price": (100 + i) * (1.05 if direction == "long" else 0.95)
                        }
                    }
                    signals.append(signal)
                
                # Create the signal timeline visualization
                signal_timeline = plot_signal_timeline(signals)
                st.plotly_chart(signal_timeline, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating signal timeline visualization: {str(e)}")
        
        with tabs[3]:  # Progression Tracker tab
            st.header("Progression Tracker")
            st.write("The progression tracker shows how trades progress through the timeframe hierarchy.")
            
            try:
                # Generate sample trades for demonstration
                trades = []
                
                for i in range(15):
                    # Use first timeframe as entry, progress through higher ones
                    entry_tf = settings["timeframes"][0]
                    progression = []
                    
                    for j in range(1, len(settings["timeframes"])):
                        # Add progression steps with 70% chance of success
                        achieved = j != 3 or i % 3 != 0  # Make some trades fail at specific point
                        
                        progression.append({
                            "target_timeframe": settings["timeframes"][j],
                            "target_price": 100 + (j * 2),
                            "achieved": achieved
                        })
                        
                        if not achieved:
                            break
                    
                    trade = {
                        "entry_timeframe": entry_tf,
                        "entry_time": datetime.now() - timedelta(days=30-i),
                        "entry_price": 100,
                        "direction": "long" if i % 2 == 0 else "short",
                        "progression": progression
                    }
                    trades.append(trade)
                
                # Create the progression tracker visualization
                progression_tracker = plot_progression_tracker(trades)
                st.plotly_chart(progression_tracker, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating progression tracker visualization: {str(e)}")
        
        with tabs[4]:  # Conflict Map tab
            st.header("Conflict Map")
            st.write("The conflict map highlights detected timeframe conflicts and their types.")
            
            try:
                # Generate sample conflicts for demonstration
                conflicts = []
                base_time = datetime.now() - timedelta(days=30)
                
                for i in range(20):
                    if len(settings["timeframes"]) >= 2:
                        # Choose two adjacent timeframes
                        tf_idx = i % (len(settings["timeframes"]) - 1)
                        higher_tf = settings["timeframes"][tf_idx + 1]
                        lower_tf = settings["timeframes"][tf_idx]
                        
                        # Choose conflict type
                        conflict_types = ["Consolidation", "DirectCorrection", "TrapSetup", "NoConflict"]
                        conflict_type = conflict_types[i % len(conflict_types)]
                        
                        conflict = {
                            "higher_timeframe": higher_tf,
                            "lower_timeframe": lower_tf,
                            "time": base_time + timedelta(days=i),
                            "type": conflict_type,
                            "risk_adjustment": -20 if conflict_type == "TrapSetup" else -10 if conflict_type == "DirectCorrection" else 0
                        }
                        conflicts.append(conflict)
                
                # Create the conflict map visualization
                conflict_map = plot_conflict_map(conflicts)
                st.plotly_chart(conflict_map, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating conflict map visualization: {str(e)}")
        
        with tabs[5]:  # Results tab
            st.header("Backtest Results")
            st.write("Detailed performance metrics and trade statistics will appear here after running a backtest.")
            
            # Use the strategy parameters component
            parameters = strategy_parameters_form()
            
            if parameters["submitted"]:
                st.success("Strategy parameters updated successfully.")
                # In a real application, we would rerun the backtest with the new parameters

def initialize_session_state():
    """Initialize session state variables"""
    if "timeframe_data" not in st.session_state:
        st.session_state.timeframe_data = None

def run_app():
    """Main function to run the Streamlit app"""
    initialize_session_state()
    configure_page()
    show_header()
    settings = sidebar_controls()
    
    # Reset session state if reset button clicked
    if settings["reset"]:
        st.session_state.timeframe_data = None
        st.experimental_rerun()
    
    main_content(settings)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_app() 