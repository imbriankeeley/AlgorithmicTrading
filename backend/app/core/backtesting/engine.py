from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..trading.strategy import MomentumStrategy, StrategyParameters
from ..trading.risk_manager import RiskManager, RiskParameters
from ...models.trade import Trade, TradeStatus, TradeType


@dataclass
class BacktestResults:
    """Container for backtest results and performance metrics."""

    trades: List[Trade]
    equity_curve: pd.Series
    performance_metrics: Dict[str, float]
    trade_metrics: Dict[str, float]
    drawdown_metrics: Dict[str, float]
    parameter_values: Dict[str, float]


@dataclass
class BacktestParameters:
    """Configuration parameters for backtesting."""

    initial_capital: float = 10000.0
    trading_fees: float = 0.001  # 0.1% per trade
    slippage: float = 0.001  # 0.1% slippage assumption
    include_fees: bool = True
    include_slippage: bool = True
    enable_fractional: bool = True  # Allow fractional positions


class BacktestingEngine:
    """
    Backtesting engine for evaluating trading strategies.
    Simulates trading with historical data, applies fees/slippage,
    and generates performance metrics.
    """

    def __init__(
        self,
        strategy: MomentumStrategy,
        risk_manager: Optional[RiskManager] = None,
        parameters: Optional[BacktestParameters] = None,
    ):
        """
        Initialize the backtesting engine.

        Args:
            strategy: Trading strategy instance to test
            risk_manager: Optional risk manager instance
            parameters: Backtest configuration parameters
        """
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager()
        self.params = parameters or BacktestParameters()
        self.trades: List[Trade] = []
        self.equity_curve: Optional[pd.Series] = None

    def _apply_slippage(self, price: float, trade_type: str) -> float:
        """
        Apply slippage to trade price.

        Args:
            price: Original price
            trade_type: 'buy' or 'sell'

        Returns:
            Adjusted price with slippage
        """
        if not self.params.include_slippage:
            return price

        # Slippage makes buys more expensive and sells cheaper
        multiplier = (
            1 + self.params.slippage
            if trade_type == "buy"
            else 1 - self.params.slippage
        )
        return price * multiplier

    def _calculate_position_size(
        self, capital: float, price: float, trade_type: str
    ) -> Tuple[float, float]:
        """
        Calculate position size and adjusted entry price.

        Args:
            capital: Available capital
            price: Entry price
            trade_type: 'buy' or 'sell'

        Returns:
            Tuple of (position_size, adjusted_price)
        """
        # Apply slippage to price
        adjusted_price = self._apply_slippage(price, trade_type)

        # Calculate base position size
        position_size = (
            capital * self.strategy.params.position_size_pct / 100
        ) / adjusted_price

        # Apply fees if enabled
        if self.params.include_fees:
            fee_cost = position_size * adjusted_price * self.params.trading_fees
            position_size -= fee_cost / adjusted_price

        # Round position size if fractional not enabled
        if not self.params.enable_fractional:
            position_size = np.floor(position_size)

        return position_size, adjusted_price

    def _execute_trade(
        self,
        trade_type: str,
        price: float,
        timestamp: datetime,
        available_capital: float,
    ) -> Optional[Trade]:
        """
        Execute a trade in the backtesting environment.

        Args:
            trade_type: 'buy' or 'sell'
            price: Entry price
            timestamp: Trade timestamp
            available_capital: Available capital for the trade

        Returns:
            Executed trade or None if invalid
        """
        # Calculate position size and adjusted price
        position_size, adjusted_price = self._calculate_position_size(
            available_capital, price, trade_type
        )

        # Skip if position size is too small
        if position_size <= 0:
            return None

        # Create trade instance
        trade = Trade(
            type=trade_type,
            status=TradeStatus.OPEN.value,
            symbol="BTC-USD",  # Default for now
            entry_price=adjusted_price,
            entry_time=timestamp,
            size=position_size,
            stop_loss=self.strategy.params.stop_loss_pct,
            take_profit=self.strategy.params.take_profit_pct,
            strategy_name="MomentumStrategy",
            fees=position_size * adjusted_price * self.params.trading_fees
            if self.params.include_fees
            else 0.0,
        )

        return trade

    def _update_equity_curve(
        self, equity_history: List[float], timestamp: datetime, current_equity: float
    ) -> None:
        """
        Update the equity curve with new data point.

        Args:
            equity_history: List of equity points
            timestamp: Current timestamp
            current_equity: Current portfolio value
        """
        equity_history.append(current_equity)
        if self.equity_curve is None:
            self.equity_curve = pd.Series(equity_history, index=[timestamp])
        else:
            self.equity_curve[timestamp] = current_equity

    def _calculate_metrics(
        self,
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        """
        Calculate performance, trade, and drawdown metrics.

        Returns:
            Tuple of (performance_metrics, trade_metrics, drawdown_metrics)
        """
        if not self.equity_curve or not self.trades:
            return {}, {}, {}

        # Calculate returns
        returns = self.equity_curve.pct_change().dropna()

        # Performance metrics
        performance_metrics = {
            "total_return": (self.equity_curve[-1] / self.equity_curve[0] - 1) * 100,
            "annualized_return": (
                (1 + (self.equity_curve[-1] / self.equity_curve[0] - 1))
                ** (
                    365
                    / (self.equity_curve.index[-1] - self.equity_curve.index[0]).days
                )
                - 1
            )
            * 100,
            "sharpe_ratio": (returns.mean() / returns.std()) * np.sqrt(252)
            if returns.std() != 0
            else 0,
            "sortino_ratio": (returns.mean() / returns[returns < 0].std())
            * np.sqrt(252)
            if len(returns[returns < 0]) > 0
            else 0,
        }

        # Trade metrics
        profitable_trades = [
            t for t in self.trades if t.realized_pnl and t.realized_pnl > 0
        ]
        trade_metrics = {
            "total_trades": len(self.trades),
            "profitable_trades": len(profitable_trades),
            "win_rate": len(profitable_trades) / len(self.trades) if self.trades else 0,
            "average_profit": np.mean([t.realized_pnl for t in profitable_trades])
            if profitable_trades
            else 0,
            "average_loss": np.mean(
                [
                    t.realized_pnl
                    for t in self.trades
                    if t.realized_pnl and t.realized_pnl <= 0
                ]
            )
            if self.trades
            else 0,
            "profit_factor": (
                sum(t.realized_pnl for t in profitable_trades)
                / abs(
                    sum(
                        t.realized_pnl
                        for t in self.trades
                        if t.realized_pnl and t.realized_pnl <= 0
                    )
                )
            )
            if self.trades
            and any(t.realized_pnl and t.realized_pnl <= 0 for t in self.trades)
            else 0,
        }

        # Drawdown metrics
        rolling_max = self.equity_curve.expanding().max()
        drawdowns = (self.equity_curve - rolling_max) / rolling_max * 100
        drawdown_metrics = {
            "max_drawdown": abs(drawdowns.min()),
            "avg_drawdown": abs(drawdowns[drawdowns < 0].mean())
            if len(drawdowns[drawdowns < 0]) > 0
            else 0,
            "max_drawdown_duration": (
                drawdowns[drawdowns < 0]
                .groupby((drawdowns[drawdowns < 0] >= 0).cumsum())
                .size()
                .max()
            )
            if len(drawdowns[drawdowns < 0]) > 0
            else 0,
        }

        return performance_metrics, trade_metrics, drawdown_metrics

    def run_backtest(self, data: pd.DataFrame) -> BacktestResults:
        """
        Run backtest simulation with historical data.

        Args:
            data: Historical price data with OHLCV columns

        Returns:
            BacktestResults with performance metrics and trade history
        """
        # Reset state
        self.trades = []
        self.equity_curve = None
        current_position = None
        available_capital = self.params.initial_capital
        equity_history = [self.params.initial_capital]

        # Generate trading signals
        signals_data = self.strategy.generate_signals(data)

        # Simulate trading
        for i in range(1, len(signals_data)):
            timestamp = signals_data.index[i]
            row = signals_data.iloc[i]
            prev_row = signals_data.iloc[i - 1]

            # Update current position value
            if current_position:
                position_value = current_position.size * row["close"] - (
                    current_position.size * row["close"] * self.params.trading_fees
                    if self.params.include_fees
                    else 0
                )
                current_equity = available_capital + position_value
                self._update_equity_curve(equity_history, timestamp, current_equity)

                # Check for exit conditions
                should_exit, exit_reason = self.strategy.should_exit_position(
                    signals_data, i
                )
                if should_exit:
                    # Apply slippage to exit price
                    exit_price = self._apply_slippage(
                        row["close"],
                        "sell" if current_position.type == "buy" else "buy",
                    )

                    # Close the position
                    current_position.close_trade(exit_price, timestamp)
                    available_capital += position_value
                    self.trades.append(current_position)
                    current_position = None
                    continue

            # Check for new trade signals
            if not current_position:
                trade_signal = self.strategy.get_trade_signal(signals_data, i)

                if trade_signal:
                    # Validate trade with risk manager
                    is_valid, reason = self.risk_manager.validate_trade(
                        trade_signal["type"],
                        available_capital
                        * self.strategy.params.position_size_pct
                        / 100,
                        trade_signal["price"],
                        trade_signal["stop_loss"],
                        trade_signal["take_profit"],
                    )

                    if is_valid:
                        # Execute the trade
                        current_position = self._execute_trade(
                            trade_signal["type"],
                            trade_signal["price"],
                            timestamp,
                            available_capital,
                        )

                        if current_position:
                            available_capital -= (
                                current_position.size * current_position.entry_price
                                + (
                                    current_position.size
                                    * current_position.entry_price
                                    * self.params.trading_fees
                                    if self.params.include_fees
                                    else 0
                                )
                            )

        # Close any remaining position at the end
        if current_position:
            exit_price = self._apply_slippage(
                signals_data.iloc[-1]["close"],
                "sell" if current_position.type == "buy" else "buy",
            )
            current_position.close_trade(exit_price, signals_data.index[-1])
            self.trades.append(current_position)

        # Calculate final metrics
        performance_metrics, trade_metrics, drawdown_metrics = self._calculate_metrics()

        return BacktestResults(
            trades=self.trades,
            equity_curve=self.equity_curve,
            performance_metrics=performance_metrics,
            trade_metrics=trade_metrics,
            drawdown_metrics=drawdown_metrics,
            parameter_values={
                "short_ema_period": self.strategy.params.short_ema_period,
                "long_ema_period": self.strategy.params.long_ema_period,
                "take_profit_pct": self.strategy.params.take_profit_pct,
                "stop_loss_pct": self.strategy.params.stop_loss_pct,
                "position_size_pct": self.strategy.params.position_size_pct,
            },
        )

    def optimize_strategy(
        self,
        data: pd.DataFrame,
        parameter_ranges: Dict[str, List[float]],
        optimization_metric: str = "sharpe_ratio",
    ) -> Tuple[Dict[str, float], BacktestResults]:
        """
        Optimize strategy parameters using grid search.

        Args:
            data: Historical price data
            parameter_ranges: Dictionary of parameters and their possible values
            optimization_metric: Metric to optimize for

        Returns:
            Tuple of (best_parameters, best_results)
        """
        best_score = float("-inf")
        best_parameters = {}
        best_results = None

        # Generate all parameter combinations
        param_keys = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())

        from itertools import product

        for params in product(*param_values):
            # Update strategy parameters
            param_dict = dict(zip(param_keys, params))
            self.strategy.params = StrategyParameters(**param_dict)

            # Run backtest with current parameters
            results = self.run_backtest(data)

            # Update best parameters if better score found
            score = results.performance_metrics.get(optimization_metric, float("-inf"))
            if score > best_score:
                best_score = score
                best_parameters = param_dict
                best_results = results

        return best_parameters, best_results
