"""
Report Generator for the Multi-Timeframe 9 EMA Extension Strategy backtester.

This module generates HTML reports from backtest results.
"""

import os
import datetime
import pandas as pd
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_html_report(data_dict, extension_results=None, reclamation_results=None, 
                         chart_paths=None, output_dir='./results'):
    """
    Generate HTML report from backtest results
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes by timeframe
    extension_results : dict, optional
        Dictionary of extension detection results by timeframe
    reclamation_results : dict, optional
        Dictionary of reclamation detection results by timeframe
    chart_paths : dict or list, optional
        Dictionary of chart paths by timeframe or list of chart paths
    output_dir : str
        Directory to save the report
    
    Returns:
    --------
    str
        Path to the generated HTML report
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for the report
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Start building HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Timeframe 9 EMA Extension Strategy - Backtest Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .timeframe-section {{
                margin-bottom: 40px;
                border: 1px solid #eee;
                border-radius: 5px;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .chart-container {{
                text-align: center;
                margin: 20px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .extension-up {{
                color: green;
                font-weight: bold;
            }}
            .extension-down {{
                color: red;
                font-weight: bold;
            }}
            .summary {{
                padding: 20px;
                background-color: #e8f4f8;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <h1>Multi-Timeframe 9 EMA Extension Strategy - Backtest Report</h1>
        <p>Report generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>This report shows the backtest results for the Multi-Timeframe 9 EMA Extension Strategy.</p>
            <p>Timeframes analyzed: {', '.join(data_dict.keys())}</p>
        </div>
    """
    
    # Process each timeframe
    for tf, data in data_dict.items():
        html_content += f"""
        <div class="timeframe-section">
            <h2>{tf} Timeframe Analysis</h2>
            
            <h3>Data Summary</h3>
            <p>Data range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}</p>
            <p>Number of bars: {len(data)}</p>
            <p>Latest price: {data['Close'].iloc[-1] if 'Close' in data.columns else 'N/A'}</p>
        """
        
        # Add extension results if available
        if extension_results and tf in extension_results:
            ext = extension_results[tf]
            ext_status = "No extension detected"
            ext_class = ""
            
            if ext.get('has_extension', False):
                if ext.get('extended_up', False):
                    ext_status = f"UPWARD EXTENSION: {ext.get('extension_percentage', 0):.2f}% (threshold: {ext.get('threshold', 0):.2f}%)"
                    ext_class = "extension-up"
                elif ext.get('extended_down', False):
                    ext_status = f"DOWNWARD EXTENSION: {ext.get('extension_percentage', 0):.2f}% (threshold: {ext.get('threshold', 0):.2f}%)"
                    ext_class = "extension-down"
            
            html_content += f"""
            <h3>Extension Analysis</h3>
            <p class="{ext_class}">{ext_status}</p>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            """
            
            for key, value in ext.items():
                if isinstance(value, (bool, int, float, str)):
                    if isinstance(value, float):
                        value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                    
                    html_content += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value_str}</td>
                    </tr>
                    """
            
            html_content += "</table>"
        
        # Add reclamation results if available
        if reclamation_results and tf in reclamation_results:
            recl = reclamation_results[tf]
            html_content += f"""
            <h3>Reclamation Analysis</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            """
            
            for key, value in recl.items():
                if isinstance(value, (bool, int, float, str)):
                    if isinstance(value, float):
                        value_str = f"{value:.4f}"
                    else:
                        value_str = str(value)
                    
                    html_content += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value_str}</td>
                    </tr>
                    """
            
            html_content += "</table>"
        
        # Add chart if available
        if chart_paths:
            chart_path = None
            
            # Check if chart_paths is a dictionary
            if isinstance(chart_paths, dict) and tf in chart_paths:
                chart_path = chart_paths[tf]
            # Or if it's a list, find the chart for this timeframe
            elif isinstance(chart_paths, list):
                for path in chart_paths:
                    if tf in os.path.basename(path):
                        chart_path = path
                        break
            
            if chart_path and os.path.exists(chart_path):
                # Read the image file and convert to base64
                with open(chart_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Add image to HTML
                html_content += f"""
                <div class="chart-container">
                    <h3>Price Chart</h3>
                    <img src="data:image/png;base64,{img_data}" alt="{tf} Timeframe Chart" style="max-width:100%;">
                </div>
                """
        
        # Close the timeframe section
        html_content += "</div>"
    
    # End HTML content
    html_content += """
    </body>
    </html>
    """
    
    # Save HTML to file
    report_path = os.path.join(output_dir, f'backtest_report_{timestamp}.html')
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"Generated HTML report: {report_path}")
    return report_path

def find_latest_chart_files(directory='./results'):
    """
    Find the most recent chart files in the results directory
    
    Parameters:
    -----------
    directory : str
        Directory to search for chart files
    
    Returns:
    --------
    list
        List of chart file paths
    """
    # Create Path object
    results_dir = Path(directory)
    
    # Check if directory exists
    if not results_dir.exists() or not results_dir.is_dir():
        logger.warning(f"Results directory not found: {directory}")
        return []
    
    # Find all PNG files
    chart_files = list(results_dir.glob('*.png'))
    
    # Sort by modification time (most recent first)
    chart_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Group by timeframe
    timeframe_files = {}
    for file in chart_files:
        filename = file.name
        # Extract timeframe from filename (assuming format like '1d_strategy_results_*.png')
        if '_strategy_results_' in filename:
            timeframe = filename.split('_strategy_results_')[0]
            # Only keep the most recent file for each timeframe
            if timeframe not in timeframe_files:
                timeframe_files[timeframe] = str(file)
    
    return list(timeframe_files.values())

def generate_latest_report(data_dict=None, extension_results=None, 
                          reclamation_results=None, output_dir='./results'):
    """
    Generate a report from the latest backtest results
    
    Parameters:
    -----------
    data_dict : dict, optional
        Dictionary of dataframes by timeframe
    extension_results : dict, optional
        Dictionary of extension detection results by timeframe
    reclamation_results : dict, optional
        Dictionary of reclamation detection results by timeframe
    output_dir : str
        Directory to save the report
    
    Returns:
    --------
    str
        Path to the generated HTML report
    """
    # Find latest chart files
    chart_paths = find_latest_chart_files(output_dir)
    
    # Generate report
    return generate_html_report(
        data_dict, 
        extension_results, 
        reclamation_results, 
        chart_paths, 
        output_dir
    ) 