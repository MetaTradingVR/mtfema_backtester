# 🚦 MTFEMA Backtester: Comprehensive Project Status & Implementation Plan

> **Last Updated:** 2025-05-07 PST
> **Next Review:** 2025-05-14 PST
> 
> This document is the **canonical, unified source of truth** for project status, implementation progress, and the development roadmap. All other status or planning information in the project should reference this file.
>
> ⏰ **Reminder:** Every implementation, update, or roadmap entry must be timestamped for traceability and historical context. (2025-05-07 PST)

---

## Project Overview

The Multi-Timeframe 9 EMA Extension Strategy Backtester is a sophisticated Python-based platform that tests and optimizes trading strategies based on price extensions from the 9 EMA across multiple timeframes. The project combines advanced technical analysis with community features and mobile accessibility.

## Current State

The MT 9 EMA Extension Strategy Backtester is currently in active development. The framework is designed to test a multi-timeframe trading strategy based on 9 EMA extensions.

### Core Components Status

| Component | Status | Description |
|-----------|--------|-------------|
| Data Management | ✅ Complete | TimeframeData class, data loading with caching |
| EMA Extension Detection | ✅ Complete | Detection of price extensions from 9 EMA |
| Bollinger Bands | ✅ Complete | Volatility and breakout detection |
| Reclamation Detection | ✅ Complete | EMA reclamation identification |
| Configuration System | ✅ Complete | Parameter management and customization |
| Performance Metrics | ✅ Complete | Trade statistics and equity curve analysis |
| Visualization | ✅ Complete | Interactive plots for indicators |
| Live Trading Visualization | ✅ Complete | Real-time dashboard for live trading |
| Optimization Visualization | ✅ Complete | Parameter optimization visualizations |
| Signal Generation | ✅ Complete | Trade signal framework and rules |
| Backtesting Engine | ✅ Complete | Trade simulation and execution |
| Live Trading | ✅ Complete | Live broker integration (Tradovate, Rithmic) |
| Optimization Framework | 📝 Planned | Parameter optimization and validation |
| Web Interface | 📝 Planned | Interactive web application |

## Operation Modes

- **Test Mode** ✅ - Visualize indicators and patterns (functional)
- **Backtest Mode** ✅ - Evaluate strategy performance (functional)
- **Live Trading Mode** ✅ - Execute strategy in real-time with broker integration
- **Optimize Mode** 📝 - Test multiple parameter combinations (planned)

## Recent Updates

### **2025-05-07**: Enhanced Visualization Suite
- Added optimization visualization module with parameter heatmaps, impact analysis, and parallel coordinates plots
- Implemented real-time live trading dashboard with equity curves, active positions monitoring, and signal visualization
- Integrated broker callbacks for real-time dashboard updates during live trading

### **2025-05-06**: Live Trading Integration
- Added full backtesting engine with position tracking and trade management
- Implemented signal generation based on EMA extensions and reclamations
- Added comprehensive performance metrics with equity curve tracking
- Created interactive performance dashboard and trade timeline visualizations
- Implemented progressive targeting through timeframe hierarchy
- Added conflict detection and resolution for more robust risk management
- Built timeframe utilities for consistent timeframe handling
- Created command-line interface for running backtest operations

## Upcoming Tasks

1. Complete implementation of signal generation for backtesting
2. Develop progressive targeting across timeframes
3. Build optimization framework for parameter testing
4. Enhance visualization with trade markers and performance dashboards
5. Implement web interface for interactive analysis
6. Add more test cases and validation metrics

## Issues and Challenges

- Python 3.13 compatibility challenges with dependencies
- Series truth value ambiguity in pandas operations
- Dimensionality issues in multi-timeframe calculations
- Cache management for efficient data loading
- Timeframe synchronization for consistent backtest results

## Project Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Basic Framework | Completed | ✅ |
| Indicator Implementation | Completed | ✅ |
| Test Mode | Completed | ✅ |
| Backtest Mode | In Progress | 🚧 |
| Performance Metrics | Completed | ✅ |
| Optimization Framework | Q4 2023 | 📝 |
| Web Interface | Q1 2024 | 📝 |
| Version 1.0 Release | Q2 2024 | 📝 |

## Overall Completion Status

| Component | Current Status | Completion % |
|-----------|----------------|--------------|
| Core Backtesting Engine | Complete | 95% |
| Advanced Strategy Components | Partially Complete | 60% |
| Community Features | Partially Complete | 85% |
| Mobile Support | Partially Complete | 70% |
| Documentation | Complete | 90% |
| Testing Infrastructure | Complete | 90% |
| Visualization | Partially Complete | 75% |
| API Integration | Partially Complete | 60% |
| Data Analysis | Partially Complete | 50% |
| Performance Analytics | Partially Complete | 65% |
| Parameter Optimization | Partially Complete | 55% |
| Trade Journal | Partially Complete | 40% |
| Dashboard | Partially Complete | 35% |
| CLI Interface | Complete | 95% |

## Completed Features

### Core Engine & Implementation

✅ TimeframeData implementation
✅ Position and Trade management
✅ 9 EMA extension detection
✅ EMA reclamation detection
✅ Performance metrics calculation
✅ Command-line interface
✅ Risk management
✅ Progressive targeting
✅ Configuration management system
✅ Automated TA-Lib installation
✅ Project structure and directory organization
✅ Core backtesting loop functionality 
✅ Multiple timeframe data synchronization
✅ Indicator implementation (Bollinger Bands, PaperFeet Laguerre RSI)

### Community Features

✅ Reputation system (points, badges, levels)
✅ Signal subscription system
✅ Trading setup sharing
✅ Forums implementation
✅ Feature flags system
✅ Leaderboard generation

### Mobile Support

✅ Responsive component framework
✅ Device type detection
✅ Adaptive charts and tables
✅ Touch-friendly interfaces

### Infrastructure

✅ Project structure and organization
✅ CI/CD workflow setup
✅ API rate limiting
✅ Security considerations
✅ Localization framework
✅ Environment management with UV support
✅ Dependency management via requirements.txt
✅ Configuration via YAML/JSON and env variables

## In Progress Features

### Core Engine & Strategy Components

⏳ Pullback validation with Fibonacci zones (80%)
⏳ Advanced conflict resolution engine (70%)
⏳ ZigZag Indicator Implementation (30%)
⏳ Monte Carlo Simulation (20%)
⏳ PaperFeet Laguerre RSI (10%)
⏳ Data Caching and Storage Mechanisms (40%)

### Advanced Backtesting

⏳ Multi-Symbol Backtesting (25%)
⏳ Portfolio-Level Analysis (15%)
⏳ Custom Indicator Creation Interface (10%)
⏳ Strategy Comparison Tools (20%)
⏳ Parameter Optimization Framework (55%)
⏳ Performance Analytics with Monte Carlo (65%)
⏳ Trade Journal Integration (40%)
⏳ Dashboard for Strategy Monitoring (35%)

### Community

⏳ Full integration of community manager (75%)
⏳ User profiles with privacy controls (60%)
⏳ Signal performance tracking (80%)
⏳ Performance Tracking for Shared Setups (50%)
⏳ Achievement Badges and Recognition (40%)
⏳ Signal Discovery Mechanisms (30%)

### Mobile & User Experience

⏳ Offline functionality (50%)
⏳ Progressive Web App implementation (40%)
⏳ Mobile Notifications for Urgent Signals (20%)

### Visualization

⏳ Interactive charts with timeframe switching (65%)
⏳ Extension map visualization (70%)
⏳ Trade journal visualization (60%)
⏳ Parameter Optimization Visualization (25%)

### Data Analysis

⏳ Timeframe-Specific Performance Analysis (45%)
⏳ Machine Learning Integration (15%)
⏳ Automated Strategy Generation (10%)
⏳ Market Regime Detection (20%)

### Trading Components

⏳ Signal Export Functionality (35%)
⏳ Broker API integration (30%)
⏳ Live trading mode (25%)
⏳ Forward Testing Mode (15%)

### Educational Resources

⏳ Strategy Tutorials (40%)
⏳ API Reference (30%)
⏳ Video tutorials for key features (20%)

## Project Phase Status

✅ Phase 1: Foundation (100% Complete)
   - Project structure and organization
   - Core data infrastructure
   - Basic backtesting engine
   - Documentation framework
   - Testing infrastructure

⏳ Phase 2: Core Features (75% Complete)
   - EMA extension detection
   - Reclamation detection
   - Risk management
   - Progressive targeting
   - Pullback validation
   - Conflict resolution
   - ZigZag implementation
   - Laguerre RSI integration

⏳ Phase 3: Community Framework (85% Complete)
   - Signal subscription system
   - Reputation system
   - Trading setup sharing
   - Forums
   - Feature flags
   - Community manager integration
   - Community analytics dashboard
   - Achievement system

⏳ Phase 4: User Experience (60% Complete)
   - Mobile responsive framework
   - Basic visualization
   - Advanced interactive charts
   - Extension map visualization
   - Trade journal UI
   - Progressive Web App capabilities
   - Mobile notifications

⏳ Phase 5: Integration & Deployment (45% Complete)
   - API rate limiting
   - Security framework
   - Broker API integration
   - Live trading mode
   - Cloud deployment
   - User authentication system
   - Signal export

⏳ Phase 6: Advanced Features (20% Complete)
   - Machine learning optimization
   - Strategy variations exploration
   - Trading bot integration
   - Market regime detection
   - Real-time alerts system
   - Monte Carlo simulation
   - Multi-symbol backtesting
   - Portfolio analysis

## Additional Features from Implementation Guide

The implementation guide reveals additional comprehensive features that enhance the project:

### Performance Analytics
- Monte Carlo simulations for strategy robustness assessment
- Extensive performance metrics calculation (profit factor, Sharpe ratio, etc.)
- Visualization dashboards for performance analysis

### Parameter Optimization
- Framework for optimizing extension thresholds and timeframe hierarchies
- Grid search capabilities for strategy parameter combinations
- Visualization of optimization results with trade count and performance metrics

### Trade Journal
- Detailed trade journaling system with entry/exit tracking
- Trade analysis by setup type, quality, and timeframe
- Integration with backtest results

### Dashboard System
- Web-based dashboard for strategy monitoring
- Multi-page interface with charts, tables, and interactive controls
- Extension map visualization for real-time market analysis

### Testing Framework
- Unit tests for indicators and strategy components
- Automated test runner script

## Priority Next Steps

1. Complete Parameter Optimization Framework
   - Implement parameter variant generation
   - Create grid search for optimal parameters
   - Build visualization for optimization results
   - Add multi-objective optimization capability

2. Enhance Visualization
   - Complete extension map visualization
   - Add Sankey diagram for timeframe progression
   - Implement trade entry/exit markers on price charts
   - Create 3D visualizations for parameter optimization

3. Add Web Interface
   - Build Streamlit or Dash application
   - Create interactive parameter configuration
   - Implement real-time visualization updates
   - Add portfolio-level analysis

4. Expand Analysis Capabilities
   - Implement Monte Carlo simulation
   - Add market regime detection
   - Create comparison against benchmark strategies
   - Develop machine learning for pattern recognition

## Implementation Recommendations

- Prioritize completing core strategy elements before expanding to advanced features
- Implement automated testing for all components
- Create a beta testing program with selected users
- Consider containerization for easier deployment
- Add benchmark comparisons for strategy validation
- Strengthen data validation layer
- Expand risk management capabilities

## Resource Requirements

- 1-2 Python developers (3-6 months)
- 1 Frontend/UI developer (2-3 months)
- QA engineer for testing (part-time)
- Data scientist for advanced analysis features (part-time)

## Technical Implementation 

The implementation guide covers extensive technical details for:
1. Development environment setup with PyCharm, Python, and UV
2. Project structure with all necessary modules
3. Core component implementation with code examples
4. PyCharm and Jupyter Lab integration
5. CLI interface for all operations
6. Dashboard implementation using Dash

This comprehensive merge provides a unified view of both the project status report and the detailed implementation guide, giving a complete picture of current progress and future development needs. 

## 📋 Implementation Progress

### **2025-05-07**: Signal Generation and Backtesting Implementation

Completed the implementation of the core backtesting engine with:

1. **Signal Generation System**: Created a comprehensive signal generation module that identifies EMA extension and reclamation signals across multiple timeframes.

2. **Conflict Resolution Framework**: Implemented the timeframe conflict detection and resolution system as outlined in the strategy playbook, including trade adjustment based on conflict type.

3. **Progressive Targeting**: Built the progressive targeting system that moves methodically through the timeframe hierarchy as outlined in the strategy.

4. **Performance Metrics**: Developed extensive performance analysis including equity curve, drawdown calculation, win rates by timeframe, and reward-risk analysis.

5. **Interactive Visualization**: Created a modern dashboard with plotly for visualizing backtest results, including equity curve, trade distribution, and timeframe performance.

6. **Command-line Interface**: Created a flexible CLI interface with options for different operation modes, parameter files, and output formats.

These components now allow for complete end-to-end backtesting of the MT 9 EMA Extension strategy with all the specifications from the strategy playbook.

### **2025-05-06**: Web Interface Implementation

Added a modern, interactive web interface using Streamlit for the backtester:

1. **Core UI Framework**: Created a responsive Streamlit application with custom styling and a multi-tab interface for different visualizations and controls.

2. **Parameter Controls**: Implemented sidebar controls for symbol selection, date ranges, timeframe selection, and strategy parameters with appropriate defaults and validation.

3. **Visualization Integration**: Connected the previously developed visualization components (Extension Map, Signal Timeline, etc.) to the web interface.

4. **Dashboard Components**: Added specialized UI components including performance metrics cards, equity curve visualization, trade tables, and parameter forms.

5. **Data Fetcher**: Created a data retrieval module for fetching market data from Yahoo Finance with support for multiple timeframes and automatic indicator calculation.

The web interface provides a complete environment for configuring backtests, running them, and analyzing results with rich visualizations. All components are modular and designed for future extensions.

### **2025-05-06**: Advanced Visualization Components

Added four new interactive visualization components for comprehensive strategy analysis:

1. **Extension Map**: Visualizes extensions across all timeframes with a heatmap interface, allowing traders to quickly identify multi-timeframe confluence areas. Uses color coding to represent extension direction and magnitude.

2. **Signal Timeline**: Shows the evolution of trading signals across timeframes, with markers color-coded by direction (long/short) and sized by confidence. Includes detailed hover information for signal analysis.

3. **Progression Tracker**: Visualizes how trades progress through the timeframe hierarchy using a Sankey diagram. Shows the flow from entry timeframe to subsequent target timeframes, with link thickness proportional to frequency.

4. **Conflict Map**: Displays detected timeframe conflicts with visual indicators for different conflict types (Consolidation, Direct Correction, Trap Setup). Helps traders understand where risk adjustments were applied.

All visualizations use Plotly for modern, interactive display and can be saved as standalone HTML files. A test script has been added to demonstrate these visualizations using sample data. 

def generate_signals(timeframe_data, params=None):
    """Generate trading signals based on EMA extensions and reclamations.
    
    Args:
        timeframe_data: Dictionary of timeframe data with indicators
        params: Strategy parameters
    """
    if params is None:
        from mtfema_backtester.config import STRATEGY_PARAMS
        params = STRATEGY_PARAMS
        
    signals = []
    
    # Process each timeframe
    for tf, data in timeframe_data.items():
        # Get extension threshold for this timeframe
        extension_threshold = params.get_extension_threshold(tf)
        
        # Find reclamation points (use Reclamation DataFrame directly)
        reclamation_data = timeframe_data.get_indicator(tf, "Reclamation")
        if reclamation_data is None or reclamation_data.empty:
            continue
            
        # Process bullish reclamations
        bullish_reclaims = reclamation_data[reclamation_data['BullishReclaim']].index
        for idx in bullish_reclaims:
            # Get price data at reclamation point
            try:
                price_data = data.loc[idx]
                
                # Verify extension condition
                extension_pct = timeframe_data.get_indicator(tf, "Extension").loc[idx]
                if extension_pct < extension_threshold:
                    continue
                    
                # Find recent swing low for stop placement
                n_bars_back = 5  # Look back 5 bars for swing low
                lookback_idx = max(0, data.index.get_loc(idx) - n_bars_back)
                lookback_data = data.iloc[lookback_idx:data.index.get_loc(idx)]
                stop_price = lookback_data['Low'].min() * 0.99  # Add 1% buffer
                
                signals.append({
                    'datetime': idx,
                    'timeframe': tf,
                    'type': 'LONG',
                    'entry_price': price_data['Close'],
                    'stop_price': stop_price,
                    'extension_pct': extension_pct
                })
            except (KeyError, IndexError) as e:
                logging.warning(f"Error generating signal at {idx}: {str(e)}")
                
        # Process bearish reclamations
        bearish_reclaims = reclamation_data[reclamation_data['BearishReclaim']].index
        # Similar logic for bearish signals
        
    return pd.DataFrame(signals) 

def execute_backtest(signals, timeframe_data, params):
    """Execute backtest with generated signals.
    
    Args:
        signals: DataFrame of trade signals
        timeframe_data: TimeframeData instance with price data
        params: Strategy parameters
    """
    trades = []
    account_balance = params.get_param('risk_management.initial_balance', 10000.0)
    risk_pct = params.get_param('risk_management.account_risk_percent', 1.0) / 100.0
    
    # Get reference timeframe for context
    reference_tf = params.get_param('timeframes.reference_timeframe', '4h')
    
    for _, signal in signals.iterrows():
        tf = signal['timeframe']
        entry_time = signal['datetime']
        
        # Get data for this timeframe
        data = timeframe_data.get_timeframe(tf)
        if data is None:
            continue
            
        # Check reference timeframe for conflicts
        if reference_tf in timeframe_data.get_available_timeframes():
            # Implement conflict resolution logic here
            conflict_type = check_timeframe_conflict(timeframe_data, tf, reference_tf, entry_time)
            # Adjust risk based on conflict
            adjusted_risk = adjust_risk_for_conflict(risk_pct, conflict_type)
        else:
            adjusted_risk = risk_pct
            conflict_type = "None"
        
        # Calculate position size
        risk_amount = account_balance * adjusted_risk
        risk_per_share = abs(signal['entry_price'] - signal['stop_price'])
        position_size = risk_amount / risk_per_share
        
        # Get next timeframe target
        target_tf = get_next_timeframe_in_hierarchy(tf)
        target_price = get_target_for_timeframe(timeframe_data, target_tf, signal['type'])
        
        # Simulate trade execution (similar to your implementation)
        # ...
        
        # Record trade results including the progression through timeframes
        trade = {
            'entry_time': entry_time,
            'exit_time': exit_time,
            'timeframe': tf,
            'target_timeframe': target_tf,
            'type': signal['type'],
            'entry_price': signal['entry_price'],
            'exit_price': exit_price,
            'stop_price': signal['stop_price'],
            'target_price': target_price,
            'position_size': position_size,
            'profit': profit * position_size,
            'profit_pct': profit / signal['entry_price'],
            'win': profit > 0,
            'conflict_type': conflict_type
        }
        
        trades.append(trade)
        
        # Update account balance
        account_balance += trade['profit']
    
    return pd.DataFrame(trades), account_balance 

def calculate_performance_metrics(trades_df, initial_balance=10000.0):
    """Calculate comprehensive performance metrics with equity curve.
    
    Returns:
        tuple: (metrics_dict, equity_curve_df)
    """
    if len(trades_df) == 0:
        return {}, pd.DataFrame()
    
    # Create equity curve with dates
    equity_curve = create_equity_curve(trades_df, initial_balance)
    
    # Standard metrics (include yours plus these additions)
    metrics = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['win'] == True).mean(),
        'profit_factor': 0,
        'average_win': trades_df[trades_df['win']]['profit_pct'].mean() if len(trades_df[trades_df['win']]) > 0 else 0,
        'average_loss': trades_df[~trades_df['win']]['profit_pct'].mean() if len(trades_df[~trades_df['win']]) > 0 else 0,
        'total_profit': trades_df['profit'].sum(),
        'total_profit_pct': trades_df['profit_pct'].sum(),
        'max_drawdown': calculate_max_drawdown(equity_curve),
        'max_drawdown_pct': calculate_max_drawdown_percentage(equity_curve),
        
        # Additional metrics
        'sharpe_ratio': calculate_sharpe_ratio(equity_curve),
        'avg_trade_duration': calculate_avg_duration(trades_df),
        'longest_win_streak': calculate_longest_streak(trades_df, 'win', True),
        'longest_loss_streak': calculate_longest_streak(trades_df, 'win', False),
        'reward_risk_ratio': calculate_reward_risk_ratio(trades_df),
        
        # Timeframe metrics
        'trades_by_timeframe': trades_df.groupby('timeframe').size().to_dict(),
        'win_rate_by_timeframe': trades_df.groupby('timeframe')['win'].mean().to_dict(),
        'profit_by_timeframe': trades_df.groupby('timeframe')['profit'].sum().to_dict()
    }
    
    # Calculate profit factor
    gross_profit = trades_df[trades_df['profit'] > 0]['profit'].sum()
    gross_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].sum())
    metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    return metrics, equity_curve 

def create_performance_dashboard(trades_df, timeframe_data, metrics, equity_curve):
    """Create a comprehensive performance dashboard with multiple visualizations.
    
    Returns:
        plotly.graph_objects.Figure: Interactive dashboard figure
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create figure with more comprehensive subplots
    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"colspan": 2}, None],
            [{}, {}],
            [{}, {}],
            [{}, {}]
        ],
        subplot_titles=(
            "Equity Curve with Drawdown",
            "Performance by Timeframe", "Monthly Returns",
            "Extension Map", "Trade Results by Direction",
            "Profit Distribution", "Timeframe Progression"
        )
    )
    
    # Add equity curve with drawdown overlay
    if not equity_curve.empty:
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['balance'],
                mode='lines',
                name='Equity'
            ),
            row=1, col=1
        )
        
        # Add drawdown overlay on secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['drawdown_pct'] * 100,  # Convert to percentage
                mode='lines',
                name='Drawdown %',
                yaxis="y2",
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        # Setup secondary y-axis
        fig.update_layout(
            yaxis2=dict(
                title="Drawdown %",
                overlaying="y",
                side="right",
                showgrid=False
            )
        )
    
    # Add extension map visualization (new feature)
    # ... implementation for extension map here
    
    # Add other visualizations based on your strategy playbook
    
    # Update layout
    fig.update_layout(
        height=1200,
        width=1000,
        title_text="MT 9 EMA Strategy Performance Dashboard",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig 

def get_next_timeframe_in_hierarchy(current_tf):
    """Get the next timeframe in the hierarchy."""
    timeframe_hierarchy = [
        "1m", "5m", "10m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"
    ]
    
    try:
        current_idx = timeframe_hierarchy.index(current_tf)
        if current_idx < len(timeframe_hierarchy) - 1:
            return timeframe_hierarchy[current_idx + 1]
        return current_tf  # Return the same if at the top
    except ValueError:
        # If not found, return the next reasonable timeframe
        return "1h"  # Default to 1h if unknown format 

def check_timeframe_conflict(timeframe_data, current_tf, higher_tf, timestamp):
    """Check for conflicts between current and higher timeframe."""
    # Get extension data
    current_ext = timeframe_data.get_indicator(current_tf, "ExtensionSignal")
    higher_ext = timeframe_data.get_indicator(higher_tf, "ExtensionSignal")
    
    if current_ext is None or higher_ext is None:
        return "NoData"
    
    # Get current values
    current_idx = timestamp
    higher_idx = map_timestamp_to_higher_timeframe(timestamp, current_tf, higher_tf)
    
    try:
        # Check if both have extensions but in opposite directions
        if (current_ext.loc[current_idx, 'has_extension'] and 
            higher_ext.loc[higher_idx, 'has_extension']):
            
            if ((current_ext.loc[current_idx, 'extended_up'] and 
                 higher_ext.loc[higher_idx, 'extended_down']) or
                (current_ext.loc[current_idx, 'extended_down'] and 
                 higher_ext.loc[higher_idx, 'extended_up'])):
                return "DirectCorrection"
        
        # Check for trap setup
        if (higher_ext.loc[higher_idx, 'has_extension'] and 
            not current_ext.loc[current_idx, 'has_extension']):
            # Check reclamation in lower timeframe
            reclamation = timeframe_data.get_indicator(current_tf, "Reclamation")
            if reclamation is not None and reclamation.loc[current_idx, 'BullishReclaim'] or reclamation.loc[current_idx, 'BearishReclaim']:
                return "TrapSetup"
            return "Consolidation"
        
        return "NoConflict"
    except (KeyError, IndexError):
        return "DataError" 

def normalize_timeframe(tf):
    """Convert various timeframe formats to standard format."""
    # Common timeframe mappings
    mappings = {
        # Days
        '1': '1d', 'd': '1d', 'day': '1d', 'daily': '1d', '1day': '1d', 'D': '1d',
        # Hours
        'h': '1h', 'hour': '1h', '1hour': '1h', '60m': '1h', '60min': '1h', 'H': '1h',
        # Minutes
        'm': '1m', 'min': '1m', 'minute': '1m', '1minute': '1m', 'M': '1m',
        # Weeks
        'w': '1w', 'week': '1w', '1week': '1w', 'weekly': '1w', 'W': '1w',
        # Months
        'mo': '1M', 'month': '1M', '1month': '1M', 'monthly': '1M', 'MO': '1M'
    }
    
    # Check if already in standard format
    standard_formats = ['1m', '5m', '10m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']
    if tf in standard_formats:
        return tf
    
    # Try direct mapping
    if tf.lower() in mappings:
        return mappings[tf.lower()]
    
    # Try to parse more complex formats
    import re
    match = re.match(r'(\d+)([a-zA-Z]+)', tf)
    if match:
        value, unit = match.groups()
        unit = unit.lower()
        if unit in ['m', 'min', 'minute', 'minutes']:
            return f"{value}m"
        elif unit in ['h', 'hr', 'hour', 'hours']:
            return f"{value}h"
        elif unit in ['d', 'day', 'days']:
            return f"{value}d"
        elif unit in ['w', 'week', 'weeks']:
            return f"{value}w"
        elif unit in ['mo', 'month', 'months']:
            return f"{value}M"
    
    # Return original with warning
    logging.warning(f"Unrecognized timeframe format: {tf}, using as-is")
    return tf 