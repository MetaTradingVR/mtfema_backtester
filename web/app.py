import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project components
from web.components import (
    create_sidebar, 
    create_parameter_controls, 
    create_symbol_search,
    create_timeframe_selector,
    display_performance_metrics,
    get_sample_data
)

# Set page configuration
st.set_page_config(
    page_title="MT 9 EMA Backtester",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
def apply_custom_css():
    st.markdown("""
    <style>
    /* ShadCN UI inspired styling */
    .main {
        background-color: #f9fafb;
        color: #111827;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f3f4f6;
        border-radius: 0.5rem;
        padding: 0.25rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #2563eb !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    /* Card styling */
    .card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    /* Button styling */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 0.375rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
    }
    /* Slider styling */
    .stSlider [data-baseweb="slider"] {
        height: 0.5rem;
    }
    .stSlider [data-baseweb="thumb"] {
        height: 1rem;
        width: 1rem;
        background-color: #2563eb;
    }
    /* Select box styling */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 0.375rem;
    }
    /* Performance metrics grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #6b7280;
        font-size: 0.875rem;
    }
    .metric-value {
        color: #111827;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }
    /* Timeline styling */
    .timeline-container {
        margin-top: 1rem;
    }
    /* Conflict map styling */
    .conflict-map-container {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# Initialize session state
if 'run_backtest' not in st.session_state:
    st.session_state.run_backtest = False
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = "ES"
if 'selected_timeframes' not in st.session_state:
    st.session_state.selected_timeframes = ["1d", "1h", "15m"]
if 'date_range' not in st.session_state:
    st.session_state.date_range = [datetime.now() - timedelta(days=365), datetime.now()]
if 'ema_period' not in st.session_state:
    st.session_state.ema_period = 9
if 'extension_threshold' not in st.session_state:
    st.session_state.extension_threshold = 0.5
if 'risk_percentage' not in st.session_state:
    st.session_state.risk_percentage = 1.0
if 'use_atr_stops' not in st.session_state:
    st.session_state.use_atr_stops = True
if 'atr_multiplier' not in st.session_state:
    st.session_state.atr_multiplier = 2.0
if 'initial_capital' not in st.session_state:
    st.session_state.initial_capital = 100000

# Main header
st.title("📊 Multi-Timeframe 9 EMA Extension Strategy Backtester")

# Create sidebar with strategy controls
create_sidebar()

# Main content area with tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Backtest Results", 
    "🔥 Extension Map", 
    "⏱️ Signal Timeline", 
    "🔄 Progression Tracker",
    "⚠️ Conflict Map"
])

# Tab 1: Backtest Results
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Main configuration
        st.subheader("Backtest Configuration")
        
        # Symbol search with suggestions
        symbol = create_symbol_search()
        
        # Timeframe selection
        timeframes = create_timeframe_selector()
        
        # Date range selector
        col1a, col1b = st.columns(2)
        with col1a:
            start_date = st.date_input("Start Date", value=st.session_state.date_range[0])
        with col1b:
            end_date = st.date_input("End Date", value=st.session_state.date_range[1])
        
        # Parameter controls (EMA, extension threshold, etc.)
        create_parameter_controls()
        
        # Run backtest button
        if st.button("Run Backtest"):
            st.session_state.run_backtest = True
            st.session_state.selected_symbol = symbol
            st.session_state.selected_timeframes = timeframes
            st.session_state.date_range = [start_date, end_date]
            
    with col2:
        # Performance metrics
        st.subheader("Performance Metrics")
        if st.session_state.run_backtest:
            # This would be replaced with actual backtest results
            display_performance_metrics()
        else:
            st.info("Run a backtest to see performance metrics.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display results charts if backtest has been run
    if st.session_state.run_backtest:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Equity Curve")
        
        # Generate sample equity curve data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        sample_equity = get_sample_data(len(dates), start=st.session_state.initial_capital)
        
        # Create equity curve chart
        fig = px.line(
            x=dates, 
            y=sample_equity,
            labels={"x": "Date", "y": "Account Value ($)"},
            title=f"{st.session_state.selected_symbol} Backtest Results"
        )
        fig.update_layout(
            height=500,
            margin=dict(l=40, r=40, t=40, b=40),
            hovermode="x unified",
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(230, 230, 230, 0.8)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(230, 230, 230, 0.8)'
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade analysis
        st.subheader("Trade Analysis")
        
        # Sample trade data
        trade_data = {
            "Entry Date": pd.date_range(start=start_date, end=end_date, freq='10D')[:20],
            "Exit Date": pd.date_range(start=start_date + timedelta(days=3), end=end_date, freq='10D')[:20],
            "Direction": np.random.choice(["Long", "Short"], size=20),
            "Entry Price": np.random.uniform(4000, 4500, size=20),
            "Exit Price": np.random.uniform(4000, 4500, size=20),
            "Profit/Loss ($)": np.random.uniform(-2000, 3000, size=20),
            "Profit/Loss (%)": np.random.uniform(-2, 3, size=20),
            "Initial Timeframe": np.random.choice(st.session_state.selected_timeframes, size=20),
            "Target Timeframe": np.random.choice(st.session_state.selected_timeframes, size=20),
        }
        
        # Calculate values
        trade_df = pd.DataFrame(trade_data)
        trade_df["Holding Period (days)"] = (trade_df["Exit Date"] - trade_df["Entry Date"]).dt.days
        
        # Style DataFrame
        def color_profit(val):
            if isinstance(val, (int, float)):
                color = 'green' if val > 0 else 'red' if val < 0 else 'black'
                return f'color: {color}'
            return ''
            
        styled_trades = trade_df.style.applymap(color_profit, subset=["Profit/Loss ($)", "Profit/Loss (%)"])
        
        st.dataframe(styled_trades, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Extension Map
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("EMA Extension Map")
    
    if st.session_state.run_backtest:
        # Create sample extension map data
        timeframes = st.session_state.selected_timeframes
        dates = pd.date_range(start=start_date, end=end_date, freq='D')[-30:]
        
        # Create sample extension values
        extensions = np.random.uniform(-2.5, 2.5, size=(len(dates), len(timeframes)))
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=extensions,
            x=timeframes,
            y=dates,
            colorscale='RdBu_r',
            zmid=0,
            colorbar=dict(
                title="Extension",
                titleside="right",
                tickmode="array",
                tickvals=[-2, -1, 0, 1, 2],
                ticktext=["-2x", "-1x", "0", "+1x", "+2x"],
            ),
            hovertemplate='Timeframe: %{x}<br>Date: %{y}<br>Extension: %{z:.2f}x<extra></extra>'
        ))
        
        fig.update_layout(
            title="9 EMA Extension Map",
            height=600,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Timeframe",
            yaxis_title="Date",
            yaxis_dtick=86400000.0 * 5,  # Show every 5 days
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <p>The Extension Map visualizes how price has extended from the 9 EMA across different timeframes. Positive values (blue) indicate price above the EMA, negative values (red) indicate price below the EMA.</p>
        <ul>
            <li>Darker colors represent stronger extensions</li>
            <li>Consistent colors across timeframes indicate multi-timeframe confluence</li>
            <li>Color transitions signal potential reversal zones</li>
        </ul>
        """, unsafe_allow_html=True)
    else:
        st.info("Run a backtest to see the Extension Map visualization.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 3: Signal Timeline
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Trading Signal Timeline")
    
    if st.session_state.run_backtest:
        # Create sample signal timeline data
        timeframes = st.session_state.selected_timeframes
        dates = pd.date_range(start=start_date, end=end_date, freq='D')[-60:]
        
        # Generate random signals (for demonstration)
        signals = []
        for tf in timeframes:
            # Generate 20-30 random signals for each timeframe
            num_signals = np.random.randint(20, 30)
            signal_dates = np.random.choice(dates, size=num_signals, replace=False)
            for date in sorted(signal_dates):
                direction = np.random.choice(["Long", "Short"])
                confidence = np.random.uniform(0.5, 1.0)
                signals.append({
                    "Date": date,
                    "Timeframe": tf,
                    "Direction": direction,
                    "Confidence": confidence,
                    "Extension": np.random.uniform(-1.5, 1.5)
                })
        
        signal_df = pd.DataFrame(signals)
        
        # Create signal timeline visualization
        fig = go.Figure()
        
        # Add long signals
        long_signals = signal_df[signal_df["Direction"] == "Long"]
        fig.add_trace(go.Scatter(
            x=long_signals["Date"],
            y=long_signals["Timeframe"],
            mode="markers",
            marker=dict(
                size=long_signals["Confidence"] * 15,
                color="green",
                symbol="triangle-up",
                opacity=0.7,
                line=dict(width=1, color="darkgreen")
            ),
            name="Long Signals",
            hovertemplate='Date: %{x}<br>Timeframe: %{y}<br>Confidence: %{marker.size:.2f}<extra></extra>'
        ))
        
        # Add short signals
        short_signals = signal_df[signal_df["Direction"] == "Short"]
        fig.add_trace(go.Scatter(
            x=short_signals["Date"],
            y=short_signals["Timeframe"],
            mode="markers",
            marker=dict(
                size=short_signals["Confidence"] * 15,
                color="red",
                symbol="triangle-down",
                opacity=0.7,
                line=dict(width=1, color="darkred")
            ),
            name="Short Signals",
            hovertemplate='Date: %{x}<br>Timeframe: %{y}<br>Confidence: %{marker.size:.2f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Trading Signal Timeline",
            height=600,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Date",
            yaxis_title="Timeframe",
            yaxis=dict(
                categoryorder="array",
                categoryarray=timeframes
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <p>The Signal Timeline shows when trading signals occurred across different timeframes. The visualization helps identify:</p>
        <ul>
            <li>Signal clusters indicating strong multi-timeframe confluence</li>
            <li>Signal progression from lower to higher timeframes</li>
            <li>Periods of high and low signal activity</li>
        </ul>
        <p>Triangle size represents signal confidence level. Hover over points for detailed information.</p>
        """, unsafe_allow_html=True)
    else:
        st.info("Run a backtest to see the Signal Timeline visualization.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 4: Progression Tracker
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Timeframe Progression Tracker")
    
    if st.session_state.run_backtest:
        # Create sample Sankey diagram data
        timeframes = st.session_state.selected_timeframes
        
        # Create nodes (timeframes)
        nodes = []
        for tf in timeframes:
            nodes.append({"name": f"Entry {tf}"})
        for tf in timeframes:
            nodes.append({"name": f"Target {tf}"})
            
        # Create links between nodes
        links = []
        node_indices = {node["name"]: i for i, node in enumerate(nodes)}
        
        for entry_tf in timeframes:
            entry_idx = node_indices[f"Entry {entry_tf}"]
            # Create random links to target timeframes
            for target_tf in timeframes:
                if timeframes.index(target_tf) >= timeframes.index(entry_tf):
                    target_idx = node_indices[f"Target {target_tf}"]
                    # Higher probability for immediately higher timeframe
                    if timeframes.index(target_tf) == timeframes.index(entry_tf) + 1:
                        value = np.random.randint(50, 100)
                    elif target_tf == entry_tf:
                        value = np.random.randint(30, 50)
                    else:
                        value = np.random.randint(5, 30)
                        
                    links.append({
                        "source": entry_idx,
                        "target": target_idx,
                        "value": value
                    })
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=[node["name"] for node in nodes],
                color=["rgba(31, 119, 180, 0.8)"] * len(timeframes) + ["rgba(255, 127, 14, 0.8)"] * len(timeframes)
            ),
            link=dict(
                source=[link["source"] for link in links],
                target=[link["target"] for link in links],
                value=[link["value"] for link in links],
                color=["rgba(0, 0, 255, 0.2)"] * len(links)
            )
        )])
        
        fig.update_layout(
            title="Timeframe Progression Flow",
            height=600,
            margin=dict(l=40, r=40, t=40, b=40),
            font=dict(size=12),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <p>The Progression Tracker visualizes how trades flow from entry timeframes to target timeframes. This Sankey diagram shows:</p>
        <ul>
            <li>How frequently trades initiated in one timeframe reach targets in higher timeframes</li>
            <li>Which entry timeframes are most effective for reaching specific targets</li>
            <li>The distribution of trade progression patterns across the timeframe hierarchy</li>
        </ul>
        <p>Wider connections indicate more frequent progressions between those timeframes.</p>
        """, unsafe_allow_html=True)
    else:
        st.info("Run a backtest to see the Progression Tracker visualization.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 5: Conflict Map
with tab5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Timeframe Conflict Map")
    
    if st.session_state.run_backtest:
        # Create sample conflict data
        timeframes = st.session_state.selected_timeframes
        
        # Create matrix of timeframe conflicts
        num_timeframes = len(timeframes)
        conflict_matrix = np.zeros((num_timeframes, num_timeframes))
        
        # Fill with sample conflict data
        for i in range(num_timeframes):
            for j in range(i+1, num_timeframes):
                # More conflicts between adjacent timeframes
                if j == i + 1:
                    conflict_matrix[i, j] = np.random.randint(20, 40)
                else:
                    # Fewer conflicts between distant timeframes
                    conflict_matrix[i, j] = np.random.randint(5, 20)
                
                # Make symmetric
                conflict_matrix[j, i] = conflict_matrix[i, j]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=conflict_matrix,
            x=timeframes,
            y=timeframes,
            colorscale='YlOrRd',
            hovertemplate='%{y} vs %{x}<br>Conflicts: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Timeframe Conflict Heatmap",
            height=600,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Timeframe",
            yaxis_title="Timeframe",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Conflict type distribution
        st.subheader("Conflict Type Distribution")
        
        # Sample conflict type data
        conflict_types = ["Consolidation", "Direct Opposition", "Trap Setup", "Momentum Divergence", "Volume Divergence"]
        conflict_counts = np.random.randint(10, 50, size=len(conflict_types))
        
        # Create bar chart
        fig2 = px.bar(
            x=conflict_types,
            y=conflict_counts,
            color=conflict_types,
            labels={"x": "Conflict Type", "y": "Count"},
            title="Conflict Type Distribution"
        )
        
        fig2.update_layout(
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("""
        <p>The Conflict Map visualizes where trading signals across different timeframes conflict with each other:</p>
        <ul>
            <li>Darker areas indicate more frequent conflicts between those timeframes</li>
            <li>Conflict types analysis helps understand the nature of these conflicts</li>
            <li>Understanding these patterns can help improve risk management during conflicting signals</li>
        </ul>
        """, unsafe_allow_html=True)
    else:
        st.info("Run a backtest to see the Conflict Map visualization.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; color: #6b7280; font-size: 0.8rem;">
    MT 9 EMA Backtester © 2025 | Version 1.0.0 | Last updated: May 6, 2025
</div>
""", unsafe_allow_html=True)

# Main entry point
if __name__ == "__main__":
    pass 