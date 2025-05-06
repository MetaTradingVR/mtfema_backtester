                'win_rate': 0,
                'profit_factor': 0,
                'total_profit': 0,
                'average_profit': 0,
                'average_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'total_return': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'avg_trade_duration': 0,
                'final_equity': self.initial_capital
            }
            return
        
        # Extract profits
        profits = [trade.get('profit', 0) for trade in self.trades]
        profit_pcts = [trade.get('profit_pct', 0) for trade in self.trades]
        
        # Calculate win/loss metrics
        winning_trades = [t for t in self.trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('profit', 0) <= 0]
        
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        
        win_rate = num_winning / self.total_trades if self.total_trades > 0 else 0
        
        # Calculate profit metrics
        total_profit = sum(profits)
        total_profit_pct = sum(profit_pcts)
        
        gross_profit = sum(t.get('profit', 0) for t in winning_trades) if winning_trades else 0
        gross_loss = sum(t.get('profit', 0) for t in losing_trades) if losing_trades else 0
        
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        avg_profit = gross_profit / num_winning if num_winning > 0 else 0
        avg_loss = gross_loss / num_losing if num_losing > 0 else 0
        
        largest_win = max(profits) if profits else 0
        largest_loss = min(profits) if profits else 0
        
        # Calculate equity curve metrics
        if self.equity_curve:
            equity_values = [point['equity'] for point in self.equity_curve]
            self.final_equity = equity_values[-1]
            
            # Calculate total return
            total_return = (self.final_equity / self.initial_capital - 1) * 100
            
            # Calculate drawdown
            max_equity = equity_values[0]
            max_drawdown = 0
            max_drawdown_pct = 0
            
            for equity in equity_values:
                max_equity = max(max_equity, equity)
                drawdown = max_equity - equity
                drawdown_pct = drawdown / max_equity * 100
                
                max_drawdown = max(max_drawdown, drawdown)
                max_drawdown_pct = max(max_drawdown_pct, drawdown_pct)
            
            # Calculate returns for Sharpe and Sortino ratios
            daily_returns = []
            prev_equity = equity_values[0]
            
            for equity in equity_values[1:]:
                daily_return = (equity / prev_equity) - 1
                daily_returns.append(daily_return)
                prev_equity = equity
            
            # Calculate Sharpe ratio (annualized)
            if daily_returns:
                avg_return = np.mean(daily_returns)
                std_return = np.std(daily_returns)
                risk_free_rate = 0.02 / 252  # Assume 2% annual risk-free rate
                
                sharpe_ratio = ((avg_return - risk_free_rate) / std_return) * np.sqrt(252) if std_return > 0 else 0
                
                # Calculate Sortino ratio (annualized)
                negative_returns = [r for r in daily_returns if r < 0]
                downside_deviation = np.std(negative_returns) if negative_returns else 0
                
                sortino_ratio = ((avg_return - risk_free_rate) / downside_deviation) * np.sqrt(252) if downside_deviation > 0 else 0
            else:
                sharpe_ratio = 0
                sortino_ratio = 0
        else:
            self.final_equity = self.initial_capital
            total_return = 0
            max_drawdown = 0
            max_drawdown_pct = 0
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Calculate average trade duration
        durations = [t.get('trade_duration', 0) for t in self.trades if t.get('trade_duration') is not None]
        avg_trade_duration = np.mean(durations) if durations else 0
        
        # Store metrics
        self.metrics = {
            'total_trades': self.total_trades,
            'winning_trades': num_winning,
            'losing_trades': num_losing,
            'win_rate': win_rate * 100,  # Convert to percentage
            'profit_factor': profit_factor,
            'total_profit': total_profit,
            'total_profit_pct': total_profit_pct,
            'average_profit': avg_profit,
            'average_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'avg_trade_duration': avg_trade_duration,
            'final_equity': self.final_equity
        }
    
    @property
    def final_equity(self) -> float:
        """Get final equity value."""
        if hasattr(self, '_final_equity'):
            return self._final_equity
        
        if self.equity_curve:
            return self.equity_curve[-1]['equity']
        else:
            return self.initial_capital
    
    @final_equity.setter
    def final_equity(self, value: float):
        """Set final equity value."""
        self._final_equity = value
    
    @property
    def total_return(self) -> float:
        """Get total return percentage."""
        return self.metrics.get('total_return', 0)
    
    @property
    def win_rate(self) -> float:
        """Get win rate percentage."""
        return self.metrics.get('win_rate', 0)
    
    @property
    def profit_factor(self) -> float:
        """Get profit factor."""
        return self.metrics.get('profit_factor', 0)
    
    @property
    def max_drawdown(self) -> float:
        """Get maximum drawdown amount."""
        return self.metrics.get('max_drawdown', 0)
    
    @property
    def max_drawdown_pct(self) -> float:
        """Get maximum drawdown percentage."""
        return self.metrics.get('max_drawdown_pct', 0)
    
    def get_equity_curve_df(self) -> pd.DataFrame:
        """
        Get equity curve as a DataFrame.
        
        Returns:
            DataFrame with timestamp and equity
        """
        if not self.equity_curve:
            return pd.DataFrame(columns=['timestamp', 'equity'])
        
        df = pd.DataFrame(self.equity_curve)
        df.set_index('timestamp', inplace=True)
        return df
    
    def get_trades_df(self) -> pd.DataFrame:
        """
        Get trades as a DataFrame.
        
        Returns:
            DataFrame with trade details
        """
        if not self.trades:
            return pd.DataFrame(columns=['symbol', 'direction', 'entry_date', 'exit_date', 'profit'])
        
        return pd.DataFrame(self.trades)
    
    def plot_equity_curve(self, figsize=(12, 6), show_drawdown=True):
        """
        Plot the equity curve.
        
        Args:
            figsize: Figure size tuple
            show_drawdown: Whether to show drawdown in a separate plot
            
        Returns:
            Matplotlib figure object
        """
        if not self.equity_curve:
            print("No equity data to plot")
            return None
        
        # Convert equity curve to DataFrame
        df = self.get_equity_curve_df()
        
        if show_drawdown:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, gridspec_kw={'height_ratios': [3, 1]})
        else:
            fig, ax1 = plt.subplots(figsize=figsize)
        
        # Plot equity curve
        ax1.plot(df.index, df['equity'], label='Equity')
        
        # Calculate and plot drawdown if requested
        if show_drawdown:
            # Calculate drawdown
            rolling_max = df['equity'].cummax()
            drawdown = (df['equity'] - rolling_max) / rolling_max * 100
            
            # Plot drawdown
            ax2.fill_between(df.index, drawdown, 0, color='red', alpha=0.3)
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_title('Drawdown')
            ax2.grid(True)
        
        # Format main plot
        ax1.set_title(f'Equity Curve - {self.strategy_name}')
        ax1.set_ylabel('Equity ($)')
        ax1.grid(True)
        
        # Add annotations
        ax1.annotate(f'Return: {self.total_return:.2f}%', xy=(0.02, 0.95), xycoords='axes fraction')
        ax1.annotate(f'Max DD: {self.max_drawdown_pct:.2f}%', xy=(0.02, 0.90), xycoords='axes fraction')
        ax1.annotate(f'Sharpe: {self.metrics.get("sharpe_ratio", 0):.2f}', xy=(0.02, 0.85), xycoords='axes fraction')
        
        plt.tight_layout()
        return fig
    
    def plot_returns_distribution(self, figsize=(10, 6)):
        """
        Plot the distribution of trade returns.
        
        Args:
            figsize: Figure size tuple
            
        Returns:
            Matplotlib figure object
        """
        if not self.trades:
            print("No trades to plot")
            return None
        
        # Extract profit percentages
        profits = [trade.get('profit_pct', 0) for trade in self.trades]
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot histogram
        n, bins, patches = ax.hist(profits, bins=30, alpha=0.7)
        
        # Color positive and negative bars differently
        for i in range(len(patches)):
            if bins[i] < 0:
                patches[i].set_facecolor('red')
            else:
                patches[i].set_facecolor('green')
        
        # Add mean line
        mean_profit = np.mean(profits)
        ax.axvline(mean_profit, color='black', linestyle='dashed', linewidth=1)
        
        # Add annotations
        ax.text(0.95, 0.95, f'Mean: {mean_profit:.2f}%', 
                verticalalignment='top', horizontalalignment='right',
                transform=ax.transAxes)
        
        ax.set_title('Trade Returns Distribution')
        ax.set_xlabel('Return (%)')
        ax.set_ylabel('Frequency')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_monthly_returns(self, figsize=(12, 6)):
        """
        Plot monthly returns heatmap.
        
        Args:
            figsize: Figure size tuple
            
        Returns:
            Matplotlib figure object
        """
        if not self.trades:
            print("No trades to plot")
            return None
        
        # Get trades DataFrame
        trades_df = self.get_trades_df()
        
        # Ensure exit_date is datetime
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        
        # Extract month and year from exit date
        trades_df['year'] = trades_df['exit_date'].dt.year
        trades_df['month'] = trades_df['exit_date'].dt.month
        
        # Calculate monthly returns
        monthly_returns = trades_df.groupby(['year', 'month'])['profit_pct'].sum().unstack()
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Generate heatmap
        im = ax.imshow(monthly_returns, cmap='RdYlGn')
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Return (%)', rotation=-90, va="bottom")
        
        # Set ticks and labels
        ax.set_xticks(np.arange(monthly_returns.shape[1]))
        ax.set_yticks(np.arange(monthly_returns.shape[0]))
        
        ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        ax.set_yticklabels(monthly_returns.index)
        
        # Show values in each cell
        for i in range(monthly_returns.shape[0]):
            for j in range(monthly_returns.shape[1]):
                value = monthly_returns.iloc[i, j]
                if pd.notna(value):
                    text_color = "black" if abs(value) < 10 else "white"
                    ax.text(j, i, f"{value:.1f}%", ha="center", va="center", color=text_color)
        
        ax.set_title('Monthly Returns (%)')
        
        plt.tight_layout()
        return fig
    
    def generate_report(self, filename: str = "backtest_report.html"):
        """
        Generate HTML report with backtest results.
        
        Args:
            filename: Path to save HTML report
            
        Returns:
            Path to saved report
        """
        import base64
        from io import BytesIO
        from datetime import datetime
        
        # Create HTML string
        html = f"""
        <html>
        <head>
            <title>Backtest Report - {self.strategy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1, h2 {{ color: #2c3e50; }}
                .container {{ margin-bottom: 30px; }}
                .metric-box {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
                .metric-title {{ font-weight: bold; font-size: 14px; color: #7f8c8d; }}
                .metric-value {{ font-size: 24px; color: #2c3e50; }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Backtest Report</h1>
            <p>Strategy: <strong>{self.strategy_name}</strong></p>
            <p>Symbols: {', '.join(self.symbols)}</p>
            <p>Timeframes: {', '.join(self.timeframes)}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="container">
                <h2>Performance Summary</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-title">Total Return</div>
                        <div class="metric-value {
                            'positive' if self.metrics['total_return'] > 0 else 'negative'
                        }">{self.metrics['total_return']:.2f}%</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-title">Win Rate</div>
                        <div class="metric-value">{self.metrics['win_rate']:.2f}%</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-title">Profit Factor</div>
                        <div class="metric-value">{self.metrics['profit_factor']:.2f}</div>
                    </div>
                    <div class="metric-box" style="flex: 1;">
                        <div class="metric-title">Max Drawdown</div>
                        <div class="metric-value negative">{self.metrics['max_drawdown_pct']:.2f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <h2>Detailed Metrics</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Initial Capital</td>
                        <td>${self.initial_capital:.2f}</td>
                    </tr>
                    <tr>
                        <td>Final Equity</td>
                        <td>${self.metrics['final_equity']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Total Profit</td>
                        <td class="{
                            'positive' if self.metrics['total_profit'] > 0 else 'negative'
                        }">${self.metrics['total_profit']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Total Trades</td>
                        <td>{self.metrics['total_trades']}</td>
                    </tr>
                    <tr>
                        <td>Winning Trades</td>
                        <td>{self.metrics['winning_trades']}</td>
                    </tr>
                    <tr>
                        <td>Losing Trades</td>
                        <td>{self.metrics['losing_trades']}</td>
                    </tr>
                    <tr>
                        <td>Average Win</td>
                        <td class="positive">${self.metrics['average_profit']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Average Loss</td>
                        <td class="negative">${self.metrics['average_loss']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Largest Win</td>
                        <td class="positive">${self.metrics['largest_win']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Largest Loss</td>
                        <td class="negative">${self.metrics['largest_loss']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Sharpe Ratio</td>
                        <td>{self.metrics['sharpe_ratio']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Sortino Ratio</td>
                        <td>{self.metrics['sortino_ratio']:.2f}</td>
                    </tr>
                    <tr>
                        <td>Avg Trade Duration</td>
                        <td>{self.metrics['avg_trade_duration']:.2f} days</td>
                    </tr>
                </table>
            </div>
        """
        
        # Generate plots and embed them in HTML
        # Equity curve
        fig = self.plot_equity_curve()
        if fig:
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            equity_curve_img = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            html += f"""
            <div class="container">
                <h2>Equity Curve</h2>
                <img src="data:image/png;base64,{equity_curve_img}" style="width: 100%; max-width: 1000px;">
            </div>
            """
        
        # Returns distribution
        fig = self.plot_returns_distribution()
        if fig:
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            returns_dist_img = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            html += f"""
            <div class="container">
                <h2>Returns Distribution</h2>
                <img src="data:image/png;base64,{returns_dist_img}" style="width: 100%; max-width: 1000px;">
            </div>
            """
        
        # Monthly returns
        fig = self.plot_monthly_returns()
        if fig:
            buffer = BytesIO()
            fig.savefig(buffer, format='png')
            buffer.seek(0)
            monthly_returns_img = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            html += f"""
            <div class="container">
                <h2>Monthly Returns</h2>
                <img src="data:image/png;base64,{monthly_returns_img}" style="width: 100%; max-width: 1000px;">
            </div>
            """
        
        # Add trades table
        if self.trades:
            trades_html = "<div class='container'><h2>Trade List</h2><table>"
            trades_html += "<tr><th>Symbol</th><th>Direction</th><th>Entry Date</th><th>Exit Date</th><th>Entry Price</th><th>Exit Price</th><th>Profit</th><th>Profit %</th><th>Reason</th></tr>"
            
            for trade in self.trades[:50]:  # Limit to first 50 trades for performance
                profit_class = "positive" if trade.get('profit', 0) > 0 else "negative"
                
                trades_html += f"""
                <tr>
                    <td>{trade.get('symbol', '')}</td>
                    <td>{trade.get('direction', '')}</td>
                    <td>{trade.get('entry_date', '')}</td>
                    <td>{trade.get('exit_date', '')}</td>
                    <td>${trade.get('entry_price', 0):.2f}</td>
                    <td>${trade.get('exit_price', 0):.2f}</td>
                    <td class="{profit_class}">${trade.get('profit', 0):.2f}</td>
                    <td class="{profit_class}">{trade.get('profit_pct', 0):.2f}%</td>
                    <td>{trade.get('exit_reason', '')}</td>
                </tr>
                """
            
            if len(self.trades) > 50:
                trades_html += f"<tr><td colspan='9'>Showing 50 of {len(self.trades)} trades</td></tr>"
                
            trades_html += "</table></div>"
            html += trades_html
        
        # Close HTML
        html += """
            </body>
        </html>
        """
        
        # Save HTML to file
        with open(filename, 'w') as f:
            f.write(html)
        
        logger.info(f"Backtest report saved to {filename}")
        return filename
    
    def save_results(self, filename: str):
        """
        Save backtest results to JSON file.
        
        Args:
            filename: File path to save results
            
        Returns:
            File path
        """
        # Prepare data for serialization
        data = {
            'strategy_name': self.strategy_name,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'initial_capital': self.initial_capital,
            'metrics': self.metrics,
            'trades': self.trades,
            'equity_curve': [
                {'timestamp': str(point['timestamp']), 'equity': point['equity']}
                for point in self.equity_curve
            ]
        }
        
        # Save to JSON
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Backtest results saved to {filename}")
        return filename
    
    @classmethod
    def load_results(cls, filename: str) -> 'BacktestResult':
        """
        Load backtest results from JSON file.
        
        Args:
            filename: Path to JSON file
            
        Returns:
            BacktestResult object
        """
        # Load from JSON
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Convert equity curve timestamps back to datetime
        equity_curve = [
            {'timestamp': pd.to_datetime(point['timestamp']), 'equity': point['equity']}
            for point in data['equity_curve']
        ]
        
        # Create result object
        result = cls(
            trades=data['trades'],
            equity_curve=equity_curve,
            initial_capital=data['initial_capital'],
            symbols=data['symbols'],
            timeframes=data['timeframes'],
            strategy_name=data['strategy_name']
        )
        
        # Update metrics
        result.metrics = data['metrics']
        
        logger.info(f"Loaded backtest results from {filename}")
        return result
