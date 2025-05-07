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
    bands : pandas.DataFrame or tuple
        DataFrame with Bollinger Bands (Upper, Middle, Lower) or a tuple of (middle_band, upper_band, lower_band)
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
        
        # Process bands based on input type
        if isinstance(bands, tuple) and len(bands) == 3:
            # Unpack tuple of (middle_band, upper_band, lower_band)
            middle_band, upper_band, lower_band = bands
        elif isinstance(bands, pd.DataFrame):
            # Check column names in DataFrame
            if 'Middle' in bands.columns:
                middle_band = bands['Middle']
                upper_band = bands['Upper'] if 'Upper' in bands.columns else None
                lower_band = bands['Lower'] if 'Lower' in bands.columns else None
            elif 'middle_band' in bands.columns:
                middle_band = bands['middle_band']
                upper_band = bands['upper_band'] if 'upper_band' in bands.columns else None
                lower_band = bands['lower_band'] if 'lower_band' in bands.columns else None
            else:
                # Try to use the first three columns
                cols = bands.columns.tolist()
                if len(cols) >= 3:
                    middle_band = bands[cols[0]]
                    upper_band = bands[cols[1]]
                    lower_band = bands[cols[2]]
                else:
                    logger.warning("Could not determine Bollinger Bands columns")
                    return None
        else:
            logger.warning("Invalid bands input format")
            return None
        
        # Add Bollinger Bands
        if middle_band is not None:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=middle_band,
                    line=dict(color='blue', width=1.5),
                    name='Middle Band (SMA)'
                )
            )
        
        if upper_band is not None:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=upper_band,
                    line=dict(color='green', width=1),
                    name='Upper Band'
                )
            )
        
        if lower_band is not None:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=lower_band,
                    line=dict(color='red', width=1),
                    name='Lower Band'
                )
            )
        
        # Add fill between bands if both upper and lower bands exist
        if upper_band is not None and lower_band is not None:
            fig.add_trace(
                go.Scatter(
                    x=data.index.tolist() + data.index.tolist()[::-1],
                    y=upper_band.tolist() + lower_band.tolist()[::-1],
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
        
        return fig
    
    except Exception as e:
        logger.error(f"Error plotting Bollinger Bands: {str(e)}")
        return None

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

def plot_extension_map(timeframe_data, timeframes=None, lookback=100, title="Multi-Timeframe Extension Map"):
    """
    Create an interactive extension map visualization showing extensions across all timeframes.
    
    Timestamp: 2025-05-06 PST
    Reference: See 'Visual Indicators for Dashboard' in strategy_playbook.md (Section 8)
    
    Parameters:
    -----------
    timeframe_data : TimeframeData
        Multi-timeframe data object containing price data and indicators
    timeframes : list, optional
        List of timeframes to include (defaults to all available timeframes)
    lookback : int, optional
        Number of periods to look back for visualization
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure showing the extension map
        
    Usage Example:
    --------------
    >>> extension_map = plot_extension_map(timeframe_data, lookback=50)
    >>> extension_map.write_html("extension_map.html")
    """
    try:
        # Get available timeframes if not specified
        if timeframes is None:
            timeframes = timeframe_data.get_available_timeframes()
            
        # Sort timeframes by duration
        timeframes = sorted(timeframes, 
                            key=lambda tf: timeframe_data.get_timeframe_minutes(tf))
        
        logger.info(f"Creating extension map for timeframes: {timeframes}")
        
        # Initialize data structures for the heatmap
        extension_data = {}
        dates = None
        
        # Collect extension data for each timeframe
        for tf in timeframes:
            # Get price data for this timeframe
            tf_data = timeframe_data.get_timeframe(tf)
            
            if tf_data is None or tf_data.empty:
                logger.warning(f"No data available for timeframe {tf}")
                continue
                
            # Get or calculate EMA and extension
            ema_col = f"EMA_9"
            if ema_col in tf_data.columns:
                ema = tf_data[ema_col]
            else:
                logger.warning(f"EMA not found for {tf}, skipping timeframe")
                continue
            
            # Calculate extension percentage
            extension = 100 * (tf_data['Close'] - ema) / ema
            
            # Limit to lookback period
            if len(tf_data) > lookback:
                extension = extension.iloc[-lookback:]
                tf_data = tf_data.iloc[-lookback:]
            
            # Store the extension data
            extension_data[tf] = extension
            
            # Use this timeframe's dates if first one processed
            if dates is None:
                dates = tf_data.index
        
        if not extension_data:
            logger.error("No extension data available for any timeframe")
            return go.Figure()
        
        # Create a figure
        fig = go.Figure()
        
        # Create a heatmap for the extension map
        z_values = []
        y_labels = timeframes
        
        # For alignment issues, we may need to reindex all series to a common date range
        all_dates = dates
        
        for tf in timeframes:
            if tf in extension_data:
                # Reindex to match the common date range
                ext = extension_data[tf]
                
                # Convert to list of values (replacing NaN with 0)
                ext_values = ext.fillna(0).tolist()
                
                # Ensure consistent length
                if len(ext_values) < len(all_dates):
                    padding = [0] * (len(all_dates) - len(ext_values))
                    ext_values = padding + ext_values
                elif len(ext_values) > len(all_dates):
                    ext_values = ext_values[-len(all_dates):]
                
                z_values.append(ext_values)
            else:
                # Add a row of zeros if data is missing
                z_values.append([0] * len(all_dates))
        
        # Create a custom colorscale:
        # - Strong negative extensions: dark red
        # - Mild negative extensions: light red
        # - No extension: white/light gray
        # - Mild positive extensions: light green
        # - Strong positive extensions: dark green
        colorscale = [
            [0.0, 'rgb(165,0,38)'],     # Strong negative (dark red)
            [0.3, 'rgb(215,48,39)'],    # Moderate negative (red)
            [0.45, 'rgb(244,109,67)'],  # Mild negative (light red)
            [0.5, 'rgb(255,255,255)'],  # Neutral (white)
            [0.55, 'rgb(186,228,174)'], # Mild positive (light green)
            [0.7, 'rgb(35,139,69)'],    # Moderate positive (green)
            [1.0, 'rgb(0,68,27)']       # Strong positive (dark green)
        ]
        
        # Create the heatmap
        heatmap = go.Heatmap(
            z=z_values,
            x=all_dates,
            y=y_labels,
            colorscale=colorscale,
            zmid=0,  # Center the color scale at 0
            zmin=-5, # Negative extension limit for color scaling
            zmax=5,  # Positive extension limit for color scaling
            colorbar=dict(
                title="Extension %",
                titleside="right",
                tickvals=[-5, -2.5, 0, 2.5, 5],
                ticktext=["-5%", "-2.5%", "0%", "+2.5%", "+5%"]
            ),
            hovertemplate="Timeframe: %{y}<br>Date: %{x}<br>Extension: %{z:.2f}%<extra></extra>"
        )
        
        fig.add_trace(heatmap)
        
        # Update layout
        fig.update_layout(
            title=title,
            height=600,
            xaxis=dict(
                title="Date/Time",
                tickformat="%Y-%m-%d %H:%M"
            ),
            yaxis=dict(
                title="Timeframe",
                tickmode="array",
                tickvals=timeframes,
                ticktext=timeframes
            ),
            template="plotly_white"
        )
        
        logger.info(f"Created extension map with {len(timeframes)} timeframes and {len(all_dates)} time periods")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating extension map: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_signal_timeline(signals, lookback=None, title="Signal Timeline"):
    """
    Create an interactive visualization of trading signals across timeframes.
    
    Timestamp: 2025-05-06 PST
    Reference: See 'Visual Indicators for Dashboard' in strategy_playbook.md (Section 8)
    
    Parameters:
    -----------
    signals : list
        List of signal dictionaries as output by the SignalGenerator
    lookback : int, optional
        Number of most recent signals to display (None = all signals)
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure showing the signal timeline
        
    Usage Example:
    --------------
    >>> signals = generate_signals(timeframe_data)
    >>> signal_timeline = plot_signal_timeline(signals, lookback=20)
    >>> signal_timeline.write_html("signal_timeline.html")
    """
    try:
        if not signals:
            logger.warning("No signals to plot")
            return go.Figure()
        
        # Limit to lookback if specified
        if lookback is not None and lookback < len(signals):
            signals = signals[-lookback:]
        
        # Extract unique timeframes from signals
        timeframes = sorted(list(set(s['timeframe'] for s in signals)))
        
        # Create a vertical spacing between timeframes
        tf_spacing = 1.0 / len(timeframes)
        tf_positions = {tf: i * tf_spacing for i, tf in enumerate(timeframes)}
        
        # Create a figure
        fig = go.Figure()
        
        # Group signals by direction
        long_signals = [s for s in signals if s['direction'] == 'long']
        short_signals = [s for s in signals if s['direction'] == 'short']
        
        # Colors and sizes based on confidence levels
        confidence_colors = {
            'high': 'rgba(0, 150, 0, 0.9)',     # Strong green for high confidence
            'medium': 'rgba(0, 180, 0, 0.7)',   # Medium green for medium confidence
            'low': 'rgba(0, 210, 0, 0.5)'       # Light green for low confidence
        }
        
        confidence_sizes = {
            'high': 12,
            'medium': 10,
            'low': 8
        }
        
        # Add long signals
        if long_signals:
            # Extract data for the plot
            times = [s['time'] for s in long_signals]
            tf_y = [tf_positions[s['timeframe']] for s in long_signals]
            colors = [confidence_colors.get(s.get('confidence', 'medium'), 'rgba(0, 180, 0, 0.7)') for s in long_signals]
            sizes = [confidence_sizes.get(s.get('confidence', 'medium'), 10) for s in long_signals]
            
            # Create hover text with signal details
            hover_texts = []
            for s in long_signals:
                target_info = s.get('target', {})
                target_price = target_info.get('target_price', 'N/A') if isinstance(target_info, dict) else 'N/A'
                target_tf = target_info.get('target_timeframe', 'N/A') if isinstance(target_info, dict) else 'N/A'
                
                hover_text = (
                    f"Direction: Long<br>"
                    f"Timeframe: {s['timeframe']}<br>"
                    f"Time: {s['time']}<br>"
                    f"Price: {s.get('price', 'N/A')}<br>"
                    f"Confidence: {s.get('confidence', 'medium')}<br>"
                    f"Target: {target_price}<br>"
                    f"Target Timeframe: {target_tf}"
                )
                hover_texts.append(hover_text)
            
            # Add the scatter plot for long signals
            fig.add_trace(go.Scatter(
                x=times,
                y=tf_y,
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    size=sizes,
                    color=colors,
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                ),
                text=hover_texts,
                hoverinfo='text',
                name='Long Signals'
            ))
        
        # Short signal colors
        short_confidence_colors = {
            'high': 'rgba(150, 0, 0, 0.9)',     # Strong red for high confidence
            'medium': 'rgba(180, 0, 0, 0.7)',   # Medium red for medium confidence
            'low': 'rgba(210, 0, 0, 0.5)'       # Light red for low confidence
        }
        
        # Add short signals
        if short_signals:
            # Extract data for the plot
            times = [s['time'] for s in short_signals]
            tf_y = [tf_positions[s['timeframe']] for s in short_signals]
            colors = [short_confidence_colors.get(s.get('confidence', 'medium'), 'rgba(180, 0, 0, 0.7)') for s in short_signals]
            sizes = [confidence_sizes.get(s.get('confidence', 'medium'), 10) for s in short_signals]
            
            # Create hover text with signal details
            hover_texts = []
            for s in short_signals:
                target_info = s.get('target', {})
                target_price = target_info.get('target_price', 'N/A') if isinstance(target_info, dict) else 'N/A'
                target_tf = target_info.get('target_timeframe', 'N/A') if isinstance(target_info, dict) else 'N/A'
                
                hover_text = (
                    f"Direction: Short<br>"
                    f"Timeframe: {s['timeframe']}<br>"
                    f"Time: {s['time']}<br>"
                    f"Price: {s.get('price', 'N/A')}<br>"
                    f"Confidence: {s.get('confidence', 'medium')}<br>"
                    f"Target: {target_price}<br>"
                    f"Target Timeframe: {target_tf}"
                )
                hover_texts.append(hover_text)
            
            # Add the scatter plot for short signals
            fig.add_trace(go.Scatter(
                x=times,
                y=tf_y,
                mode='markers',
                marker=dict(
                    symbol='triangle-down',
                    size=sizes,
                    color=colors,
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                ),
                text=hover_texts,
                hoverinfo='text',
                name='Short Signals'
            ))
        
        # Add horizontal separators between timeframes
        for i, tf in enumerate(timeframes[:-1]):
            y_pos = (tf_positions[tf] + tf_positions[timeframes[i+1]]) / 2
            fig.add_shape(
                type="line",
                x0=0,
                y0=y_pos,
                x1=1,
                y1=y_pos,
                line=dict(
                    color="rgba(0, 0, 0, 0.1)",
                    width=1,
                    dash="dot",
                ),
                xref="paper",
                yref="y"
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            height=500,
            xaxis=dict(
                title="Signal Time",
                tickformat="%Y-%m-%d %H:%M",
            ),
            yaxis=dict(
                title="Timeframe",
                tickmode="array",
                tickvals=list(tf_positions.values()),
                ticktext=list(tf_positions.keys()),
                showgrid=True
            ),
            template="plotly_white",
            hovermode="closest",
            showlegend=True
        )
        
        logger.info(f"Created signal timeline with {len(signals)} signals across {len(timeframes)} timeframes")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating signal timeline: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_progression_tracker(trades, title="Timeframe Progression Tracker"):
    """
    Create an interactive visualization showing how trades progress through the timeframe hierarchy.
    
    Timestamp: 2025-05-06 PST
    Reference: See 'Progression Tracker' in strategy_playbook.md (Section 8)
    
    Parameters:
    -----------
    trades : list
        List of completed trade dictionaries with progression information
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure showing the progression tracker
        
    Usage Example:
    --------------
    >>> trades = get_completed_trades()
    >>> progression = plot_progression_tracker(trades)
    >>> progression.write_html("progression_tracker.html")
    """
    try:
        if not trades:
            logger.warning("No trades to plot progression")
            return go.Figure()
        
        # Get all timeframes involved in the trades
        all_timeframes = set()
        for trade in trades:
            if 'entry_timeframe' in trade:
                all_timeframes.add(trade['entry_timeframe'])
            if 'progression' in trade:
                for step in trade['progression']:
                    if 'target_timeframe' in step:
                        all_timeframes.add(step['target_timeframe'])
        
        # Create a sorted list of timeframes
        timeframes = sorted(list(all_timeframes), 
                           key=lambda tf: int(''.join(filter(str.isdigit, tf))) if any(c.isdigit() for c in tf) else 0)
        
        # Map timeframes to node indices for the Sankey diagram
        tf_to_idx = {tf: i for i, tf in enumerate(timeframes)}
        
        # Initialize source, target, and value arrays for Sankey diagram
        source = []
        target = []
        value = []
        
        # Count progressions between timeframes
        progression_counts = {}
        
        for trade in trades:
            if 'entry_timeframe' not in trade or 'progression' not in trade:
                continue
                
            entry_tf = trade['entry_timeframe']
            prev_tf = entry_tf
            
            for step in trade['progression']:
                if 'target_timeframe' not in step or 'achieved' not in step:
                    continue
                    
                target_tf = step['target_timeframe']
                achieved = step['achieved']
                
                if achieved:
                    # Record this progression
                    key = (prev_tf, target_tf)
                    if key in progression_counts:
                        progression_counts[key] += 1
                    else:
                        progression_counts[key] = 1
                    
                    prev_tf = target_tf
        
        # Convert counts to Sankey diagram format
        for (source_tf, target_tf), count in progression_counts.items():
            source.append(tf_to_idx[source_tf])
            target.append(tf_to_idx[target_tf])
            value.append(count)
        
        # If no progressions found, return empty figure
        if not source:
            logger.warning("No progression data found in trades")
            return go.Figure()
        
        # Generate colors for nodes and links
        node_colors = ['rgba(44, 160, 44, 0.8)'] * len(timeframes)  # Green for nodes
        
        # Create gradient colors for links based on progression distance
        link_colors = []
        for s, t in zip(source, target):
            # Calculate progression distance (how many steps in hierarchy)
            distance = abs(timeframes.index(timeframes[t]) - timeframes.index(timeframes[s]))
            # Darker green for shorter progressions, lighter for longer
            opacity = max(0.3, min(0.7, 0.3 + 0.1 * distance))
            link_colors.append(f'rgba(44, 160, 44, {opacity})')
        
        # Create the Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=timeframes,
                color=node_colors
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=link_colors,
                hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
            )
        )])
        
        # Update layout
        fig.update_layout(
            title=title,
            font=dict(size=12),
            height=600,
            template="plotly_white"
        )
        
        logger.info(f"Created progression tracker with {len(timeframes)} timeframes and {len(source)} progression paths")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating progression tracker: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()

def plot_conflict_map(conflicts, timeframes=None, lookback=100, title="Timeframe Conflict Map"):
    """
    Create an interactive visualization of timeframe conflicts.
    
    Timestamp: 2025-05-06 PST
    Reference: See 'Conflict Display' in strategy_playbook.md (Section 8)
    
    Parameters:
    -----------
    conflicts : list
        List of conflict dictionaries with timeframe, time, and type information
    timeframes : list, optional
        List of timeframes to include (defaults to all timeframes in conflicts)
    lookback : int, optional
        Number of most recent conflicts to display
    title : str, optional
        Plot title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure showing the conflict map
        
    Usage Example:
    --------------
    >>> conflicts = detect_conflicts(timeframe_data)
    >>> conflict_map = plot_conflict_map(conflicts, lookback=50)
    >>> conflict_map.write_html("conflict_map.html")
    """
    try:
        if not conflicts:
            logger.warning("No conflicts to plot")
            return go.Figure()
        
        # Limit to lookback if needed
        if lookback and len(conflicts) > lookback:
            conflicts = conflicts[-lookback:]
        
        # Extract timeframes if not provided
        if timeframes is None:
            all_timeframes = set()
            for conflict in conflicts:
                all_timeframes.add(conflict.get('higher_timeframe', ''))
                all_timeframes.add(conflict.get('lower_timeframe', ''))
            
            timeframes = sorted([tf for tf in all_timeframes if tf],
                               key=lambda tf: int(''.join(filter(str.isdigit, tf))) if any(c.isdigit() for c in tf) else 0)
        
        # Create figure
        fig = go.Figure()
        
        # Group conflicts by type
        conflict_types = {
            'Consolidation': [],
            'DirectCorrection': [],
            'TrapSetup': [],
            'NoConflict': []
        }
        
        for conflict in conflicts:
            ctype = conflict.get('type', 'NoConflict')
            if ctype in conflict_types:
                conflict_types[ctype].append(conflict)
        
        # Colors for conflict types
        colors = {
            'Consolidation': 'rgba(255, 165, 0, 0.7)',    # Orange
            'DirectCorrection': 'rgba(255, 0, 0, 0.7)',   # Red
            'TrapSetup': 'rgba(128, 0, 128, 0.7)',        # Purple
            'NoConflict': 'rgba(0, 128, 0, 0.7)'          # Green
        }
        
        symbols = {
            'Consolidation': 'circle',
            'DirectCorrection': 'x',
            'TrapSetup': 'diamond',
            'NoConflict': 'square'
        }
        
        # Add traces for each conflict type
        for ctype, conflicts_list in conflict_types.items():
            if not conflicts_list:
                continue
                
            times = [c.get('time', '') for c in conflicts_list]
            labels = [f"{c.get('higher_timeframe', '')} ↔ {c.get('lower_timeframe', '')}" for c in conflicts_list]
            
            # Create hover text
            hover_texts = []
            for c in conflicts_list:
                hover_text = (
                    f"Conflict Type: {ctype}<br>"
                    f"Higher Timeframe: {c.get('higher_timeframe', 'N/A')}<br>"
                    f"Lower Timeframe: {c.get('lower_timeframe', 'N/A')}<br>"
                    f"Time: {c.get('time', 'N/A')}<br>"
                    f"Risk Adjustment: {c.get('risk_adjustment', '0')}%"
                )
                hover_texts.append(hover_text)
            
            # Add scatter plot for this conflict type
            fig.add_trace(go.Scatter(
                x=times,
                y=labels,
                mode='markers',
                marker=dict(
                    size=10,
                    color=colors.get(ctype, 'rgba(128, 128, 128, 0.7)'),
                    symbol=symbols.get(ctype, 'circle'),
                    line=dict(width=1, color='rgba(0, 0, 0, 0.5)')
                ),
                text=hover_texts,
                hoverinfo='text',
                name=ctype
            ))
        
        # Update layout
        fig.update_layout(
            title=title,
            height=500,
            xaxis=dict(
                title="Time",
                tickformat="%Y-%m-%d %H:%M"
            ),
            yaxis=dict(
                title="Timeframe Pair",
                categoryorder='array',
                categoryarray=labels if 'labels' in locals() else None
            ),
            template="plotly_white",
            hovermode="closest",
            showlegend=True
        )
        
        logger.info(f"Created conflict map with {len(conflicts)} conflicts")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating conflict map: {str(e)}")
        # Return simple empty figure on error
        return go.Figure()
