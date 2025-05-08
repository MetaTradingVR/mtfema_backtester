import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
import os

def create_extension_map(extensions_df, title="9 EMA Extension Map"):
    """
    Create a heatmap visualization of EMA extensions across timeframes.
    
    Args:
        extensions_df (pd.DataFrame): DataFrame with dates as index, timeframes as columns, 
                                     and extension values as cells
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive extension map figure
    """
    # Sort timeframes by duration
    sorted_timeframes = sort_timeframes(extensions_df.columns)
    sorted_extensions = extensions_df[sorted_timeframes]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=sorted_extensions.values,
        x=sorted_timeframes,
        y=sorted_extensions.index,
        colorscale='RdBu_r',  # Red for negative, Blue for positive
        zmid=0,  # Center the color scale at 0
        colorbar=dict(
            title="Extension",
            titleside="right",
            tickmode="array",
            tickvals=[-2, -1, 0, 1, 2],
            ticktext=["-2x", "-1x", "0", "+1x", "+2x"],
        ),
        hovertemplate=(
            "Timeframe: %{x}<br>" +
            "Date: %{y}<br>" +
            "Extension: %{z:.2f}x<extra></extra>"
        )
    ))
    
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="Timeframe",
        yaxis_title="Date",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    
    return fig


def create_signal_timeline(signals_df, title="Trading Signal Timeline"):
    """
    Create a timeline visualization of trading signals across timeframes.
    
    Args:
        signals_df (pd.DataFrame): DataFrame with columns for Date, Timeframe, Direction, Confidence
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive signal timeline figure
    """
    # Ensure signals are sorted by timeframe
    all_timeframes = signals_df['Timeframe'].unique()
    sorted_timeframes = sort_timeframes(all_timeframes)
    
    fig = go.Figure()
    
    # Add long signals
    long_signals = signals_df[signals_df["Direction"] == "Long"]
    if not long_signals.empty:
        fig.add_trace(go.Scatter(
            x=long_signals["Date"],
            y=long_signals["Timeframe"],
            mode="markers",
            marker=dict(
                size=long_signals["Confidence"] * 15,  # Size based on confidence
                color="green",
                symbol="triangle-up",
                opacity=0.7,
                line=dict(width=1, color="darkgreen")
            ),
            name="Long Signals",
            hovertemplate=(
                "Date: %{x}<br>" +
                "Timeframe: %{y}<br>" +
                "Confidence: %{marker.size:.2f}<extra></extra>"
            )
        ))
    
    # Add short signals
    short_signals = signals_df[signals_df["Direction"] == "Short"]
    if not short_signals.empty:
        fig.add_trace(go.Scatter(
            x=short_signals["Date"],
            y=short_signals["Timeframe"],
            mode="markers",
            marker=dict(
                size=short_signals["Confidence"] * 15,  # Size based on confidence
                color="red",
                symbol="triangle-down",
                opacity=0.7,
                line=dict(width=1, color="darkred")
            ),
            name="Short Signals",
            hovertemplate=(
                "Date: %{x}<br>" +
                "Timeframe: %{y}<br>" +
                "Confidence: %{marker.size:.2f}<extra></extra>"
            )
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="Date",
        yaxis_title="Timeframe",
        yaxis=dict(
            categoryorder="array",
            categoryarray=sorted_timeframes
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
    
    return fig


def create_progression_tracker(progression_data, title="Timeframe Progression Flow"):
    """
    Create a Sankey diagram visualization of how trades progress through timeframes.
    
    Args:
        progression_data (dict): Dictionary with nodes and links for the Sankey diagram
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive progression tracker figure
    """
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=progression_data['node_labels'],
            color=progression_data['node_colors']
        ),
        link=dict(
            source=progression_data['link_sources'],
            target=progression_data['link_targets'],
            value=progression_data['link_values'],
            color=progression_data['link_colors']
        )
    )])
    
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(size=12),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    return fig


def create_conflict_map(conflict_matrix, timeframes, title="Timeframe Conflict Heatmap"):
    """
    Create a heatmap visualization of conflicts between timeframes.
    
    Args:
        conflict_matrix (np.ndarray): 2D array with conflict counts between timeframes
        timeframes (list): List of timeframe strings
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive conflict map figure
    """
    # Sort timeframes by duration
    sorted_timeframes = sort_timeframes(timeframes)
    
    # Reorder the conflict matrix accordingly
    sorted_indices = [timeframes.index(tf) for tf in sorted_timeframes]
    sorted_matrix = conflict_matrix[sorted_indices, :][:, sorted_indices]
    
    fig = go.Figure(data=go.Heatmap(
        z=sorted_matrix,
        x=sorted_timeframes,
        y=sorted_timeframes,
        colorscale='YlOrRd',  # Yellow-Orange-Red scale
        hovertemplate=(
            "%{y} vs %{x}<br>" +
            "Conflicts: %{z}<extra></extra>"
        )
    ))
    
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="Timeframe",
        yaxis_title="Timeframe",
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    return fig


def create_conflict_type_chart(conflict_types, conflict_counts, title="Conflict Type Distribution"):
    """
    Create a bar chart visualization of conflict types.
    
    Args:
        conflict_types (list): List of conflict type names
        conflict_counts (list): List of conflict counts corresponding to types
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive conflict type chart
    """
    fig = px.bar(
        x=conflict_types,
        y=conflict_counts,
        color=conflict_types,
        labels={"x": "Conflict Type", "y": "Count"},
        title=title
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False
    )
    
    return fig


def create_equity_curve(dates, equity_values, title="Equity Curve"):
    """
    Create a line chart visualization of equity curve.
    
    Args:
        dates (list): List of dates
        equity_values (list): List of equity values
        title (str): Chart title
        
    Returns:
        plotly.graph_objects.Figure: Interactive equity curve figure
    """
    fig = px.line(
        x=dates, 
        y=equity_values,
        labels={"x": "Date", "y": "Account Value ($)"},
        title=title
    )
    
    # Add drawdown shading
    max_equity = pd.Series(equity_values).cummax()
    drawdowns = [(max_equity[i] - equity_values[i]) / max_equity[i] * 100 if max_equity[i] > 0 else 0 
                for i in range(len(equity_values))]
    
    # Add drawdown line
    fig.add_trace(go.Scatter(
        x=dates,
        y=max_equity,
        fill='tonexty',
        mode='none',
        fillcolor='rgba(255, 0, 0, 0.1)',
        showlegend=False,
        hoverinfo='skip'
    ))
    
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
    
    return fig


def sort_timeframes(timeframes):
    """
    Sort timeframes by duration from smallest to largest.
    
    Args:
        timeframes (list): List of timeframe strings
        
    Returns:
        list: Sorted list of timeframes
    """
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
    
    return sorted(timeframes, key=get_timeframe_minutes)


def save_figure(fig, filename, output_dir="output"):
    """
    Save a plotly figure to a file.
    
    Args:
        fig (plotly.graph_objects.Figure): Plotly figure to save
        filename (str): Output filename
        output_dir (str): Output directory
        
    Returns:
        str: Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Add timestamp to filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{filename}_{timestamp}.html")
    
    # Save the figure
    fig.write_html(output_path)
    
    return output_path


def generate_sample_extension_data(timeframes, dates):
    """
    Generate sample extension data for testing.
    
    Args:
        timeframes (list): List of timeframe strings
        dates (list): List of dates
        
    Returns:
        pd.DataFrame: DataFrame with extensions data
    """
    # Create empty DataFrame
    df = pd.DataFrame(index=dates, columns=timeframes)
    
    # Generate random walks for each timeframe with correlation
    base_walk = np.random.normal(0, 1, size=len(dates))
    
    for i, tf in enumerate(timeframes):
        # Higher timeframes have lower volatility
        volatility = 1.0 / (i + 1)
        
        # Higher correlation to base walk for higher timeframes
        correlation = 0.5 + 0.5 * (i / len(timeframes))
        
        # Generate correlated random walk
        tf_walk = correlation * base_walk + (1 - correlation) * np.random.normal(0, volatility, size=len(dates))
        
        # Add trend component
        trend = np.linspace(-1, 1, len(dates))
        if i % 2 == 0:  # Alternate trend direction
            trend = -trend
            
        # Combine components
        extensions = tf_walk + trend * 0.5
        
        # Scale to reasonable extension values
        extensions = extensions * 0.5
        
        df[tf] = extensions
    
    return df


def generate_sample_signals_data(timeframes, dates, num_signals=100):
    """
    Generate sample signal data for testing.
    
    Args:
        timeframes (list): List of timeframe strings
        dates (list): List of dates
        num_signals (int): Number of signals to generate
        
    Returns:
        pd.DataFrame: DataFrame with signal data
    """
    # Random sample of dates and timeframes
    random_dates = np.random.choice(dates, size=num_signals)
    random_timeframes = np.random.choice(timeframes, size=num_signals)
    
    # Generate directions and confidence
    directions = np.random.choice(["Long", "Short"], size=num_signals)
    confidences = np.random.uniform(0.5, 1.0, size=num_signals)
    
    # Create DataFrame
    signals_df = pd.DataFrame({
        "Date": random_dates,
        "Timeframe": random_timeframes,
        "Direction": directions,
        "Confidence": confidences,
        "Extension": np.random.uniform(-1.5, 1.5, size=num_signals)
    })
    
    return signals_df


def generate_sample_progression_data(timeframes):
    """
    Generate sample progression data for Sankey diagram.
    
    Args:
        timeframes (list): List of timeframe strings
        
    Returns:
        dict: Dictionary with Sankey diagram data
    """
    # Create nodes for entry and target timeframes
    node_labels = []
    for tf in timeframes:
        node_labels.append(f"Entry {tf}")
    for tf in timeframes:
        node_labels.append(f"Target {tf}")
    
    # Node colors
    node_colors = ["rgba(31, 119, 180, 0.8)"] * len(timeframes) + ["rgba(255, 127, 14, 0.8)"] * len(timeframes)
    
    # Create links
    link_sources = []
    link_targets = []
    link_values = []
    link_colors = []
    
    for i, entry_tf in enumerate(timeframes):
        for j, target_tf in enumerate(timeframes):
            # Only create links to higher or equal timeframes
            if timeframes.index(target_tf) >= timeframes.index(entry_tf):
                # Higher probability for immediately higher timeframe
                if timeframes.index(target_tf) == timeframes.index(entry_tf) + 1:
                    value = np.random.randint(50, 100)
                elif target_tf == entry_tf:
                    value = np.random.randint(30, 50)
                else:
                    value = np.random.randint(5, 30)
                
                link_sources.append(i)
                link_targets.append(len(timeframes) + j)
                link_values.append(value)
                link_colors.append("rgba(0, 0, 255, 0.2)")
    
    return {
        'node_labels': node_labels,
        'node_colors': node_colors,
        'link_sources': link_sources,
        'link_targets': link_targets,
        'link_values': link_values,
        'link_colors': link_colors
    }


def generate_sample_conflict_data(timeframes):
    """
    Generate sample conflict data for testing.
    
    Args:
        timeframes (list): List of timeframe strings
        
    Returns:
        tuple: (conflict_matrix, conflict_types, conflict_counts)
    """
    # Create conflict matrix
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
    
    # Sample conflict types
    conflict_types = ["Consolidation", "Direct Opposition", "Trap Setup", "Momentum Divergence", "Volume Divergence"]
    conflict_counts = np.random.randint(10, 50, size=len(conflict_types))
    
    return conflict_matrix, conflict_types, conflict_counts 