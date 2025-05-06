import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

logger = logging.getLogger(__name__)

def plot_ema_extension(data, ema, extension, signals=None, title="9 EMA Extension Analysis"):
    """
    Create an interactive plot of price data with EMA and extension analysis
    
    Parameters:
    -----------
    data : pandas.DataFrame
        OHLCV price data
    ema : pandas.Series
        EMA values
    extension : pandas.Series
        Extension percentage values
    signals : dict or pandas.Series, optional
        Either a dictionary with signal information or a binary signal series
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Create subplot figure with 2 rows
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[title, "Extension %"],
            row_heights=[0.7, 0.3]
        )
        
        # Add price candlestick to top subplot
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add EMA line to top subplot
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ema,
                line=dict(color='blue', width=1.5),
                name='EMA'
            ),
            row=1, col=1
        )
        
        # Add extension percentage to bottom subplot
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=extension,
                line=dict(color='purple', width=1.5),
                name='Extension %'
            ),
            row=2, col=1
        )
        
        # Add horizontal lines for extension thresholds
        threshold = 1.0  # Default threshold (can be modified later)
        
        fig.add_hline(
            y=threshold, 
            line_dash="dash", 
            line_color="green",
            annotation_text=f"+{threshold}%",
            annotation_position="right",
            row=2, col=1
        )
        
        fig.add_hline(
            y=-threshold, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"-{threshold}%",
            annotation_position="right",
            row=2, col=1
        )
        
        # Add zero line
        fig.add_hline(
            y=0, 
            line_dash="solid", 
            line_color="gray",
            line_width=0.5,
            row=2, col=1
        )
        
        # Add signals if provided
        if signals is not None:
            if isinstance(signals, dict):
                # Handle dictionary signals (from detect_9ema_extension)
                if signals.get('extended_up', False):
                    # Add a single marker at the last point
                    fig.add_trace(
                        go.Scatter(
                            x=[data.index[-1]],
                            y=[data['High'].iloc[-1] * 1.005],
                            mode='markers',
                            marker=dict(symbol='triangle-down', size=10, color='green'),
                            name='Extended Up'
                        ),
                        row=1, col=1
                    )
                
                if signals.get('extended_down', False):
                    # Add a single marker at the last point
                    fig.add_trace(
                        go.Scatter(
                            x=[data.index[-1]],
                            y=[data['Low'].iloc[-1] * 0.995],
                            mode='markers',
                            marker=dict(symbol='triangle-up', size=10, color='red'),
                            name='Extended Down'
                        ),
                        row=1, col=1
                    )
            else:
                # Handle Series signals
                # Find extended up points
                extended_up = data[signals == 1].index
                if len(extended_up) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=extended_up,
                            y=data.loc[extended_up, 'High'] * 1.005,  # Place markers slightly above highs
                            mode='markers',
                            marker=dict(symbol='triangle-down', size=10, color='green'),
                            name='Extended Up'
                        ),
                        row=1, col=1
                    )
                
                # Find extended down points
                extended_down = data[signals == -1].index
                if len(extended_down) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=extended_down,
                            y=data.loc[extended_down, 'Low'] * 0.995,  # Place markers slightly below lows
                            mode='markers',
                            marker=dict(symbol='triangle-up', size=10, color='red'),
                            name='Extended Down'
                        ),
                        row=1, col=1
                    )
        
        # Update layout
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        # Customize price subplot
        fig.update_yaxes(title_text="Price", row=1, col=1)
        
        # Customize extension subplot
        fig.update_yaxes(title_text="Extension %", row=2, col=1)
        
        logger.info(f"Created EMA Extension plot with {len(data)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating EMA Extension plot: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_bollinger_bands(data, bands, signals=None, title="Bollinger Bands Analysis"):
    """
    Create an interactive plot of price data with Bollinger Bands
    
    Parameters:
    -----------
    data : pandas.DataFrame
        OHLCV price data
    bands : pandas.DataFrame
        DataFrame with Bollinger Bands (Upper, Middle, Lower)
    signals : pandas.Series, optional
        Binary signal series (1 for breakout up, -1 for breakout down)
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Create subplot figure
        fig = make_subplots(
            rows=1, 
            cols=1,
            subplot_titles=[title]
        )
        
        # Add price candlestick
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            )
        )
        
        # Add Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=bands['Middle'],
                line=dict(color='blue', width=1.5),
                name='Middle Band (SMA)'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=bands['Upper'],
                line=dict(color='green', width=1),
                name='Upper Band'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=bands['Lower'],
                line=dict(color='red', width=1),
                name='Lower Band'
            )
        )
        
        # Add fill between bands
        fig.add_trace(
            go.Scatter(
                x=data.index.tolist() + data.index.tolist()[::-1],
                y=bands['Upper'].tolist() + bands['Lower'].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo='skip',
                showlegend=False
            )
        )
        
        # Add signals if provided
        if signals is not None and not signals.empty:
            # Find breakout up points
            breakout_up = data[signals == 1].index
            if len(breakout_up) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=breakout_up,
                        y=data.loc[breakout_up, 'High'] * 1.005,  # Place markers slightly above highs
                        mode='markers',
                        marker=dict(symbol='circle', size=8, color='green'),
                        name='Breakout Up'
                    )
                )
            
            # Find breakout down points
            breakout_down = data[signals == -1].index
            if len(breakout_down) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=breakout_down,
                        y=data.loc[breakout_down, 'Low'] * 0.995,  # Place markers slightly below lows
                        mode='markers',
                        marker=dict(symbol='circle', size=8, color='red'),
                        name='Breakout Down'
                    )
                )
        
        # Update layout
        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        logger.info(f"Created Bollinger Bands plot with {len(data)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating Bollinger Bands plot: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_zigzag(data, zigzag, title="ZigZag Swing Points"):
    """
    Create an interactive plot with ZigZag swing points
    
    Parameters:
    -----------
    data : pandas.DataFrame
        OHLCV price data
    zigzag : pandas.Series
        ZigZag values (non-zero only at swing points)
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Create figure
        fig = go.Figure()
        
        # Add price candlestick
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            )
        )
        
        # Extract swing points (non-zero values in zigzag)
        swing_points = zigzag[zigzag != 0]
        
        # Get indices of swing points
        swing_indices = swing_points.index
        
        # Extract consecutive pairs of swing points to draw lines
        lines = []
        for i in range(len(swing_indices) - 1):
            idx1 = swing_indices[i]
            idx2 = swing_indices[i + 1]
            
            # Get the dataframe indices for these swing points
            idx1_pos = data.index.get_loc(idx1)
            idx2_pos = data.index.get_loc(idx2)
            
            # Extract the subset of data between these points
            subset_indices = data.index[idx1_pos:idx2_pos + 1]
            
            lines.append({
                'x': [idx1, idx2],
                'y': [swing_points[idx1], swing_points[idx2]]
            })
        
        # Add zigzag lines
        for line in lines:
            fig.add_trace(
                go.Scatter(
                    x=line['x'],
                    y=line['y'],
                    mode='lines',
                    line=dict(color='purple', width=2),
                    showlegend=False
                )
            )
        
        # Add markers for swing points
        fig.add_trace(
            go.Scatter(
                x=swing_indices,
                y=swing_points,
                mode='markers',
                marker=dict(size=8, color='red'),
                name='Swing Points'
            )
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=600,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        logger.info(f"Created ZigZag plot with {len(swing_points)} swing points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating ZigZag plot: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_paperfeet(data, paperfeet, title="PaperFeet Indicator"):
    """
    Create an interactive plot with PaperFeet (Laguerre RSI) indicator
    
    Parameters:
    -----------
    data : pandas.DataFrame
        OHLCV price data
    paperfeet : pandas.Series
        PaperFeet (Laguerre RSI) values
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Create subplot figure with 2 rows
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[title, "PaperFeet (Laguerre RSI)"],
            row_heights=[0.7, 0.3]
        )
        
        # Add price candlestick to top subplot
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Create color mapping for PaperFeet values
        colors = []
        for value in paperfeet:
            if value < 0.15:  # Very oversold - bright red
                colors.append('rgb(255, 0, 0)')
            elif value < 0.3:  # Oversold - red
                colors.append('rgb(220, 50, 50)')
            elif value < 0.45:  # Neutral but leaning bearish - light red
                colors.append('rgb(220, 150, 150)')
            elif value < 0.55:  # Neutral - gray
                colors.append('rgb(150, 150, 150)')
            elif value < 0.7:  # Neutral but leaning bullish - light green
                colors.append('rgb(150, 220, 150)')
            elif value < 0.85:  # Overbought - green
                colors.append('rgb(50, 220, 50)')
            else:  # Very overbought - bright green
                colors.append('rgb(0, 255, 0)')
        
        # Add PaperFeet bar chart to bottom subplot with color coding
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=paperfeet,
                marker_color=colors,
                name='PaperFeet'
            ),
            row=2, col=1
        )
        
        # Add horizontal lines for overbought/oversold levels
        fig.add_hline(
            y=0.15, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Oversold",
            annotation_position="right",
            row=2, col=1
        )
        
        fig.add_hline(
            y=0.85, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Overbought",
            annotation_position="right",
            row=2, col=1
        )
        
        fig.add_hline(
            y=0.5, 
            line_dash="solid", 
            line_color="gray",
            line_width=0.5,
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        # Customize price subplot
        fig.update_yaxes(title_text="Price", row=1, col=1)
        
        # Customize PaperFeet subplot
        fig.update_yaxes(
            title_text="PaperFeet", 
            range=[0, 1],  # Fixed range for PaperFeet
            row=2, col=1
        )
        
        logger.info(f"Created PaperFeet plot with {len(data)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating PaperFeet plot: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_multi_timeframe_overview(data_dict, indicator_name='EMA_9', title="Multi-Timeframe Overview"):
    """
    Create a multi-timeframe overview plot with the same indicator across timeframes
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with timeframes as keys and DataFrames with indicators as values
    indicator_name : str
        Name of the indicator to plot across timeframes
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Get the number of timeframes
        n_timeframes = len(data_dict)
        
        if n_timeframes == 0:
            logger.warning("No data provided for multi-timeframe overview")
            return go.Figure()
            
        # Calculate subplot dimensions based on number of timeframes
        n_cols = min(2, n_timeframes)  # Max 2 columns
        n_rows = (n_timeframes + n_cols - 1) // n_cols  # Ceiling division
        
        # Create subplot titles
        subplot_titles = [f"{tf.upper()} Timeframe" for tf in data_dict.keys()]
        
        # Create subplot figure
        fig = make_subplots(
            rows=n_rows, 
            cols=n_cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # Add traces for each timeframe
        row, col = 1, 1
        for tf, data in data_dict.items():
            # Check if the data has 'Close' and the indicator
            if 'Close' not in data.columns or indicator_name not in data.columns:
                logger.warning(f"Data for {tf} missing Close or {indicator_name}")
                continue
                
            # Add price candlestick
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name=f'{tf} Price',
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Add indicator line
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[indicator_name],
                    line=dict(color='blue', width=1.5),
                    name=f'{tf} {indicator_name}',
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Update to next subplot position
            col += 1
            if col > n_cols:
                col = 1
                row += 1
        
        # Update layout
        fig.update_layout(
            title=title,
            height=300 * n_rows,
            template='plotly_white',
            xaxis_rangeslider_visible=False,
        )
        
        # Disable rangeslider for all subplots
        for i in range(1, n_timeframes + 1):
            fig.update_xaxes(rangeslider_visible=False, row=(i-1)//n_cols + 1, col=(i-1)%n_cols + 1)
        
        logger.info(f"Created multi-timeframe overview with {n_timeframes} timeframes")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating multi-timeframe overview: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_combined_strategy(data, indicators, signals, title="Combined Strategy"):
    """
    Create a comprehensive plot with all strategy components
    
    Parameters:
    -----------
    data : pandas.DataFrame
        OHLCV price data
    indicators : dict
        Dictionary of indicator DataFrames/Series
    signals : pandas.Series
        Strategy signals (1 for long, -1 for short, 0 for neutral)
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    try:
        # Create subplot figure with 3 rows
        fig = make_subplots(
            rows=3, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[title, "Extension %", "Indicators"],
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Add price candlestick to top subplot
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add EMA line to top subplot if available
        if 'EMA_9' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=indicators['EMA_9'],
                    line=dict(color='blue', width=1.5),
                    name='9 EMA'
                ),
                row=1, col=1
            )
        
        # Add Bollinger Bands to top subplot if available
        if 'BollingerBands' in indicators:
            bb = indicators['BollingerBands']
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb['middle'],
                    line=dict(color='purple', width=1),
                    name='BB SMA'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb['upper'],
                    line=dict(color='green', width=1, dash='dash'),
                    name='BB Upper'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb['lower'],
                    line=dict(color='red', width=1, dash='dash'),
                    name='BB Lower'
                ),
                row=1, col=1
            )
        
        # Add extension percentage to middle subplot if available
        if 'Extension' in indicators:
            extension = indicators['Extension']
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=extension,
                    line=dict(color='purple', width=1.5),
                    name='Extension %'
                ),
                row=2, col=1
            )
            
            # Add horizontal lines for extension thresholds
            threshold = 1.0  # Default threshold
            
            fig.add_hline(
                y=threshold, 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"+{threshold}%",
                annotation_position="right",
                row=2, col=1
            )
            
            fig.add_hline(
                y=-threshold, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"-{threshold}%",
                annotation_position="right",
                row=2, col=1
            )
            
            fig.add_hline(
                y=0, 
                line_dash="solid", 
                line_color="gray",
                line_width=0.5,
                row=2, col=1
            )
        
        # Add PaperFeet to bottom subplot if available
        if 'PaperFeet' in indicators:
            paperfeet = indicators['PaperFeet']
            
            # Create color mapping for PaperFeet values
            colors = []
            for value in paperfeet:
                if value < 0.15:  # Very oversold - bright red
                    colors.append('rgb(255, 0, 0)')
                elif value < 0.3:  # Oversold - red
                    colors.append('rgb(220, 50, 50)')
                elif value < 0.45:  # Neutral but leaning bearish - light red
                    colors.append('rgb(220, 150, 150)')
                elif value < 0.55:  # Neutral - gray
                    colors.append('rgb(150, 150, 150)')
                elif value < 0.7:  # Neutral but leaning bullish - light green
                    colors.append('rgb(150, 220, 150)')
                elif value < 0.85:  # Overbought - green
                    colors.append('rgb(50, 220, 50)')
                else:  # Very overbought - bright green
                    colors.append('rgb(0, 255, 0)')
            
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=paperfeet,
                    marker_color=colors,
                    name='PaperFeet'
                ),
                row=3, col=1
            )
            
            # Add horizontal lines for overbought/oversold levels
            fig.add_hline(
                y=0.15, 
                line_dash="dash", 
                line_color="red",
                annotation_text="OS",
                annotation_position="right",
                row=3, col=1
            )
            
            fig.add_hline(
                y=0.85, 
                line_dash="dash", 
                line_color="green",
                annotation_text="OB",
                annotation_position="right",
                row=3, col=1
            )
        
        # Add strategy signals
        if signals is not None and not signals.empty:
            # Find long entry points
            long_entries = data[signals == 1].index
            if len(long_entries) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=long_entries,
                        y=data.loc[long_entries, 'Low'] * 0.995,  # Place markers below lows
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=12, color='green'),
                        name='Long Entry'
                    ),
                    row=1, col=1
                )
            
            # Find short entry points
            short_entries = data[signals == -1].index
            if len(short_entries) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=short_entries,
                        y=data.loc[short_entries, 'High'] * 1.005,  # Place markers above highs
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=12, color='red'),
                        name='Short Entry'
                    ),
                    row=1, col=1
                )
            
            # Find exit points
            exits = data[signals == 0].index
            if len(exits) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=exits,
                        y=data.loc[exits, 'Close'],
                        mode='markers',
                        marker=dict(symbol='x', size=10, color='black'),
                        name='Exit'
                    ),
                    row=1, col=1
                )
        
        # Update layout
        fig.update_layout(
            height=900,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        # Customize price subplot
        fig.update_yaxes(title_text="Price", row=1, col=1)
        
        # Customize extension subplot
        fig.update_yaxes(title_text="Extension %", row=2, col=1)
        
        # Customize indicators subplot
        if 'PaperFeet' in indicators:
            fig.update_yaxes(
                title_text="PaperFeet", 
                range=[0, 1],
                row=3, col=1
            )
        
        logger.info(f"Created combined strategy plot with {len(data)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating combined strategy plot: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()
