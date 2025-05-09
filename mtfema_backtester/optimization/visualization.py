"""
Visualization module for the optimization framework.

This module provides functions for visualizing optimization results
with interactive charts and plots.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import os
import json

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    logger.warning("Plotly not available. Advanced visualizations will be disabled.")
    PLOTLY_AVAILABLE = False

class OptimizationVisualizer:
    """
    Class for visualizing optimization results.
    """
    
    def __init__(self, results: List[Dict[str, Any]], 
                 target_metric: str = 'sharpe_ratio',
                 output_dir: str = "./optimization_viz"):
        """
        Initialize the visualization with optimization results.
        
        Args:
            results: List of optimization results (each is a dict with 'params' and 'metrics')
            target_metric: The primary metric that was optimized
            output_dir: Directory to save visualizations
        """
        self.results = results
        self.target_metric = target_metric
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Convert results to DataFrame for easier analysis
        self.results_df = self._convert_results_to_df()
        
        logger.info(f"Initialized visualization with {len(results)} optimization results")
    
    def _convert_results_to_df(self) -> pd.DataFrame:
        """Convert optimization results to a DataFrame."""
        if not self.results:
            return pd.DataFrame()
            
        # Initialize lists to store parameter values and metrics
        data = []
        
        for result in self.results:
            # Skip invalid results
            if 'params' not in result or 'metrics' not in result:
                continue
                
            # Create a row with all parameters and metrics
            row = {}
            
            # Add parameters
            for param_name, param_value in result['params'].items():
                # Convert non-scalar parameters to strings for the DataFrame
                if isinstance(param_value, (list, dict, tuple)):
                    param_value = str(param_value)
                row[f"param_{param_name}"] = param_value
                
            # Add metrics
            for metric_name, metric_value in result['metrics'].items():
                # Skip non-numeric metrics
                if not isinstance(metric_value, (int, float)):
                    continue
                row[f"metric_{metric_name}"] = metric_value
                
            data.append(row)
            
        # Create DataFrame
        return pd.DataFrame(data)
    
    def create_parameter_importance_chart(self, save: bool = True) -> Optional[go.Figure]:
        """
        Create a parameter importance chart.
        
        Args:
            save: Whether to save the chart to disk
            
        Returns:
            Plotly figure object if plotly is available, None otherwise
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Cannot create parameter importance chart.")
            return None
            
        if self.results_df.empty:
            logger.warning("No valid results to create parameter importance chart.")
            return None
            
        # Get parameter columns
        param_cols = [col for col in self.results_df.columns if col.startswith('param_')]
        if not param_cols:
            logger.warning("No parameter columns found in results DataFrame.")
            return None
            
        # Get target metric column
        target_col = f"metric_{self.target_metric}"
        if target_col not in self.results_df.columns:
            logger.warning(f"Target metric column {target_col} not found in results DataFrame.")
            return None
            
        # Calculate parameter importance based on correlation
        importance = {}
        for param_col in param_cols:
            # Skip non-numeric parameters or those with only one unique value
            if not pd.api.types.is_numeric_dtype(self.results_df[param_col]) or self.results_df[param_col].nunique() <= 1:
                continue
                
            # Calculate correlation with target metric
            corr = self.results_df[[param_col, target_col]].corr().iloc[0, 1]
            
            # Use absolute correlation as importance
            importance[param_col.replace('param_', '')] = abs(corr)
            
        if not importance:
            logger.warning("No valid parameter importance could be calculated.")
            return None
            
        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        # Create figure
        fig = go.Figure()
        
        # Add bar chart
        fig.add_trace(
            go.Bar(
                x=list(importance.keys()),
                y=list(importance.values()),
                marker_color='rgb(55, 83, 109)',
                text=[f"{v:.3f}" for v in importance.values()],
                textposition='auto'
            )
        )
        
        # Update layout
        fig.update_layout(
            title=f"Parameter Importance for {self.target_metric}",
            xaxis_title="Parameter",
            yaxis_title="Importance (Absolute Correlation)",
            xaxis=dict(tickangle=-45),
            yaxis=dict(range=[0, 1]),
            height=600,
            margin=dict(l=50, r=50, t=80, b=100)
        )
        
        # Save figure if requested
        if save:
            file_path = self.output_dir / "parameter_importance.html"
            fig.write_html(str(file_path))
            logger.info(f"Parameter importance chart saved to {file_path}")
            
        return fig
    
    def create_parallel_coordinates_plot(self, top_n: int = 50, save: bool = True) -> Optional[go.Figure]:
        """
        Create a parallel coordinates plot for the top N parameter combinations.
        
        Args:
            top_n: Number of top results to include
            save: Whether to save the chart to disk
            
        Returns:
            Plotly figure object if plotly is available, None otherwise
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Cannot create parallel coordinates plot.")
            return None
            
        if self.results_df.empty:
            logger.warning("No valid results to create parallel coordinates plot.")
            return None
            
        # Get parameter columns
        param_cols = [col for col in self.results_df.columns if col.startswith('param_')]
        if not param_cols:
            logger.warning("No parameter columns found in results DataFrame.")
            return None
            
        # Get metric columns
        metric_cols = [col for col in self.results_df.columns if col.startswith('metric_')]
        if not metric_cols:
            logger.warning("No metric columns found in results DataFrame.")
            return None
            
        # Get target metric column
        target_col = f"metric_{self.target_metric}"
        if target_col not in self.results_df.columns:
            logger.warning(f"Target metric column {target_col} not found in results DataFrame.")
            return None
            
        # Sort by target metric and get top N
        df_sorted = self.results_df.sort_values(target_col, ascending=False).head(top_n).copy()
        
        # Clean up column names for display
        df_sorted.columns = [col.replace('param_', '').replace('metric_', '') for col in df_sorted.columns]
        
        # Only include numeric parameters and metrics
        numeric_cols = [col for col in df_sorted.columns if pd.api.types.is_numeric_dtype(df_sorted[col])]
        
        # Create a copy with numeric columns only
        df_numeric = df_sorted[numeric_cols].copy()
        
        # Create figure
        fig = px.parallel_coordinates(
            df_numeric,
            color=self.target_metric,
            labels={col: col for col in df_numeric.columns},
            color_continuous_scale=px.colors.sequential.Viridis,
            title=f"Parallel Coordinates Plot for Top {top_n} Parameter Combinations"
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            margin=dict(l=50, r=50, t=80, b=50),
            coloraxis_colorbar=dict(title=self.target_metric)
        )
        
        # Save figure if requested
        if save:
            file_path = self.output_dir / "parallel_coordinates.html"
            fig.write_html(str(file_path))
            logger.info(f"Parallel coordinates plot saved to {file_path}")
            
        return fig
    
    def create_scatter_matrix(self, top_n: int = 100, save: bool = True) -> Optional[go.Figure]:
        """
        Create a scatter matrix plot for the top N parameter combinations.
        
        Args:
            top_n: Number of top results to include
            save: Whether to save the chart to disk
            
        Returns:
            Plotly figure object if plotly is available, None otherwise
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Cannot create scatter matrix plot.")
            return None
            
        if self.results_df.empty:
            logger.warning("No valid results to create scatter matrix plot.")
            return None
            
        # Get parameter columns
        param_cols = [col for col in self.results_df.columns if col.startswith('param_')]
        if not param_cols:
            logger.warning("No parameter columns found in results DataFrame.")
            return None
            
        # Get target metric column
        target_col = f"metric_{self.target_metric}"
        if target_col not in self.results_df.columns:
            logger.warning(f"Target metric column {target_col} not found in results DataFrame.")
            return None
            
        # Sort by target metric and get top N
        df_sorted = self.results_df.sort_values(target_col, ascending=False).head(top_n).copy()
        
        # Clean up column names for display
        df_sorted.columns = [col.replace('param_', '').replace('metric_', '') for col in df_sorted.columns]
        
        # Only include numeric parameters
        numeric_params = [col for col in df_sorted.columns 
                         if col.startswith('param_') and pd.api.types.is_numeric_dtype(df_sorted[col])]
        
        # Create a subset with numeric parameters and target metric
        df_subset = df_sorted[[col for col in df_sorted.columns 
                              if not col.startswith('metric_') or col == self.target_metric]].copy()
        
        # Create figure
        dimensions = [dict(label=col, values=df_subset[col]) for col in df_subset.columns 
                     if pd.api.types.is_numeric_dtype(df_subset[col]) and df_subset[col].nunique() > 1]
        
        if len(dimensions) < 3:
            logger.warning("Not enough numeric dimensions for scatter matrix plot.")
            return None
            
        fig = px.scatter_matrix(
            df_subset,
            dimensions=[dim['label'] for dim in dimensions],
            color=self.target_metric,
            labels={col: col for col in df_subset.columns},
            title=f"Parameter Relationships for Top {top_n} Combinations"
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            width=800,
            title=dict(x=0.5),
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Save figure if requested
        if save:
            file_path = self.output_dir / "scatter_matrix.html"
            fig.write_html(str(file_path))
            logger.info(f"Scatter matrix plot saved to {file_path}")
            
        return fig
    
    def create_parameter_heatmap(self, param1: str, param2: str, save: bool = True) -> Optional[go.Figure]:
        """
        Create a heatmap for two parameters.
        
        Args:
            param1: First parameter name (without 'param_' prefix)
            param2: Second parameter name (without 'param_' prefix)
            save: Whether to save the chart to disk
            
        Returns:
            Plotly figure object if plotly is available, None otherwise
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Cannot create parameter heatmap.")
            return None
            
        if self.results_df.empty:
            logger.warning("No valid results to create parameter heatmap.")
            return None
            
        # Get parameter columns
        param1_col = f"param_{param1}"
        param2_col = f"param_{param2}"
        
        if param1_col not in self.results_df.columns:
            logger.warning(f"Parameter column {param1_col} not found in results DataFrame.")
            return None
            
        if param2_col not in self.results_df.columns:
            logger.warning(f"Parameter column {param2_col} not found in results DataFrame.")
            return None
            
        # Get target metric column
        target_col = f"metric_{self.target_metric}"
        if target_col not in self.results_df.columns:
            logger.warning(f"Target metric column {target_col} not found in results DataFrame.")
            return None
            
        # Check if parameters are numeric or have few unique values
        if not (pd.api.types.is_numeric_dtype(self.results_df[param1_col]) or 
                self.results_df[param1_col].nunique() <= 20):
            logger.warning(f"Parameter {param1} is not numeric or has too many unique values.")
            return None
            
        if not (pd.api.types.is_numeric_dtype(self.results_df[param2_col]) or 
                self.results_df[param2_col].nunique() <= 20):
            logger.warning(f"Parameter {param2} is not numeric or has too many unique values.")
            return None
            
        # Create pivot table
        pivot = self.results_df.pivot_table(
            values=target_col,
            index=param2_col,
            columns=param1_col,
            aggfunc='mean'
        )
        
        # Create figure
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Viridis',
            colorbar=dict(title=self.target_metric)
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Parameter Heatmap: {param1} vs {param2}",
            xaxis_title=param1,
            yaxis_title=param2,
            height=600,
            width=800
        )
        
        # Save figure if requested
        if save:
            file_path = self.output_dir / f"heatmap_{param1}_vs_{param2}.html"
            fig.write_html(str(file_path))
            logger.info(f"Parameter heatmap saved to {file_path}")
            
        return fig
    
    def create_optimization_dashboard(self, top_n: int = 50, save: bool = True) -> Optional[go.Figure]:
        """
        Create a comprehensive optimization dashboard.
        
        Args:
            top_n: Number of top results to include
            save: Whether to save the dashboard to disk
            
        Returns:
            Plotly figure object if plotly is available, None otherwise
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available. Cannot create optimization dashboard.")
            return None
            
        if self.results_df.empty:
            logger.warning("No valid results to create optimization dashboard.")
            return None
            
        # Get target metric column
        target_col = f"metric_{self.target_metric}"
        if target_col not in self.results_df.columns:
            logger.warning(f"Target metric column {target_col} not found in results DataFrame.")
            return None
            
        # Sort by target metric and get top N
        df_sorted = self.results_df.sort_values(target_col, ascending=False).head(top_n).copy()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[
                [{"type": "bar"}, {"type": "table"}],
                [{"type": "scatter", "colspan": 2}, None]
            ],
            subplot_titles=[
                "Parameter Importance", 
                "Top Parameter Combinations",
                "Parameter Values vs. Performance"
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        # Add parameter importance chart (top-left)
        param_cols = [col for col in self.results_df.columns if col.startswith('param_')]
        importance = {}
        
        for param_col in param_cols:
            # Skip non-numeric parameters or those with only one unique value
            if not pd.api.types.is_numeric_dtype(self.results_df[param_col]) or self.results_df[param_col].nunique() <= 1:
                continue
                
            # Calculate correlation with target metric
            corr = self.results_df[[param_col, target_col]].corr().iloc[0, 1]
            
            # Use absolute correlation as importance
            importance[param_col.replace('param_', '')] = abs(corr)
        
        if importance:
            # Sort by importance
            importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            
            fig.add_trace(
                go.Bar(
                    x=list(importance.keys()),
                    y=list(importance.values()),
                    marker_color='rgb(55, 83, 109)',
                ),
                row=1, col=1
            )
            
            # Update axes
            fig.update_xaxes(title_text="Parameter", tickangle=-45, row=1, col=1)
            fig.update_yaxes(title_text="Importance", range=[0, 1], row=1, col=1)
        
        # Add top combinations table (top-right)
        top_df = df_sorted.head(10).copy()
        
        # Clean up column names
        top_df.columns = [col.replace('param_', '').replace('metric_', '') for col in top_df.columns]
        
        # Select relevant columns for the table
        table_cols = [col for col in top_df.columns if not col.startswith('metric_') or col == self.target_metric]
        table_df = top_df[table_cols].sort_values(self.target_metric, ascending=False)
        
        # Format values
        for col in table_df.columns:
            if pd.api.types.is_numeric_dtype(table_df[col]):
                table_df[col] = table_df[col].apply(lambda x: f"{x:.4f}" if abs(x) < 100 else f"{x:.1f}")
        
        # Add table
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(table_df.columns),
                    fill_color='rgb(55, 83, 109)',
                    align='left',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[table_df[col] for col in table_df.columns],
                    fill_color='rgb(245, 245, 245)',
                    align='left'
                )
            ),
            row=1, col=2
        )
        
        # Add parameter vs. performance scatter plots (bottom)
        # Find top 3 most important parameters
        top_params = list(importance.keys())[:3] if importance else []
        
        if top_params:
            for i, param in enumerate(top_params):
                param_col = f"param_{param}"
                
                # Check if parameter is numeric
                if not pd.api.types.is_numeric_dtype(self.results_df[param_col]):
                    continue
                    
                fig.add_trace(
                    go.Scatter(
                        x=self.results_df[param_col],
                        y=self.results_df[target_col],
                        mode='markers',
                        name=param,
                        marker=dict(
                            size=8,
                            opacity=0.7,
                            line=dict(width=0.5, color='white')
                        )
                    ),
                    row=2, col=1
                )
            
            # Update axes
            fig.update_xaxes(title_text="Parameter Value", row=2, col=1)
            fig.update_yaxes(title_text=self.target_metric, row=2, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"Optimization Dashboard for {self.target_metric}",
            height=900,
            showlegend=True,
            legend=dict(orientation="h", y=0.02, yanchor="bottom"),
            margin=dict(l=60, r=40, t=100, b=60)
        )
        
        # Save figure if requested
        if save:
            file_path = self.output_dir / "optimization_dashboard.html"
            fig.write_html(str(file_path))
            logger.info(f"Optimization dashboard saved to {file_path}")
            
        return fig

def visualize_optimization_results(
    results: List[Dict[str, Any]],
    target_metric: str = 'sharpe_ratio',
    output_dir: str = "./optimization_viz"
) -> None:
    """
    Create and save visualizations for optimization results.
    
    Args:
        results: List of optimization results
        target_metric: The primary metric that was optimized
        output_dir: Directory to save visualizations
    """
    # Create visualizer
    visualizer = OptimizationVisualizer(results, target_metric, output_dir)
    
    # Create and save visualizations
    visualizer.create_parameter_importance_chart()
    visualizer.create_parallel_coordinates_plot()
    visualizer.create_scatter_matrix()
    visualizer.create_optimization_dashboard()
    
    # Try to create some parameter heatmaps with common parameters
    common_params = [
        ('ema.period', 'risk_management.reward_risk_ratio'),
        ('ema.extension_thresholds.1h', 'ema.extension_thresholds.4h'),
        ('ema.extension_thresholds.1h', 'ema.period'),
        ('risk_management.reward_risk_ratio', 'risk_management.account_risk_percent')
    ]
    
    for param1, param2 in common_params:
        try:
            visualizer.create_parameter_heatmap(param1, param2)
        except Exception as e:
            logger.warning(f"Could not create heatmap for {param1} vs {param2}: {str(e)}")
    
    logger.info(f"All optimization visualizations saved to {output_dir}") 