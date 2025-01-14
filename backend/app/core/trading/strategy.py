from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime


@dataclass
class StrategyParameters:
    """Configuration parameters for the trading strategy."""

    short_ema_period: int = 9
    long_ema_period: int = 21
    take_profit_pct: float = 2.0
    stop_loss_pct: float = 1.0
    position_size_pct: float = 1.0
    min_volume: float = 1000.0  # Minimum 24h volume in USD
    max_spread_pct: float = 0.5  # Maximum allowed spread as percentage


class MomentumStrategy:
    """
    Momentum-based trading strategy using EMA crossovers.
    Implements position sizing, risk management, and signal generation.
    """

    def __init__(self, parameters: Optional[StrategyParameters] = None):
        """
        Initialize the strategy with configurable parameters.

        Args:
            parameters: Strategy configuration parameters
        """
        self.params = parameters or StrategyParameters()
        self.current_position: Optional[Dict] = None
        self.last_signal: Optional[str] = None

    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average for given prices.

        Args:
            prices: Series of price data
            period: EMA period

        Returns:
            Series containing EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on EMA crossover.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with added signal indicators
        """
        df = data.copy()

        # Calculate EMAs
        df["short_ema"] = self.calculate_ema(df["close"], self.params.short_ema_period)
        df["long_ema"] = self.calculate_ema(df["close"], self.params.long_ema_period)

        # Generate crossover signals
        df["signal"] = 0
        df.loc[df["short_ema"] > df["long_ema"], "signal"] = 1  # Bullish
        df.loc[df["short_ema"] < df["long_ema"], "signal"] = -1  # Bearish

        # Detect actual crossovers
        df["signal_change"] = df["signal"].diff()

        return df

    def calculate_position_size(self, capital: float, current_price: float) -> float:
        """
        Calculate position size based on available capital and risk parameters.

        Args:
            capital: Available trading capital
            current_price: Current asset price

        Returns:
            Position size in base currency
        """
        position_value = capital * (self.params.position_size_pct / 100)
        return position_value / current_price

    def validate_trade_conditions(
        self, data: pd.DataFrame, index: int
    ) -> Tuple[bool, str]:
        """
        Validate market conditions for trade entry.

        Args:
            data: Market data DataFrame
            index: Current index in DataFrame

        Returns:
            Tuple of (is_valid, reason)
        """
        row = data.iloc[index]

        # Check trading volume
        if row["volume"] < self.params.min_volume:
            return False, "Insufficient volume"

        # Check spread
        if "ask" in data.columns and "bid" in data.columns:
            spread_pct = (row["ask"] - row["bid"]) / row["bid"] * 100
            if spread_pct > self.params.max_spread_pct:
                return False, "Spread too high"

        return True, "Valid"

    def get_trade_signal(self, data: pd.DataFrame, index: int) -> Optional[Dict]:
        """
        Generate trade signal based on strategy conditions.

        Args:
            data: Market data DataFrame with indicators
            index: Current index in DataFrame

        Returns:
            Dictionary with trade parameters or None
        """
        if index < 1:  # Need at least one previous candle
            return None

        row = data.iloc[index]
        prev_row = data.iloc[index - 1]

        # Check for signal change
        if row["signal_change"] == 0:
            return None

        # Validate market conditions
        is_valid, reason = self.validate_trade_conditions(data, index)
        if not is_valid:
            return None

        signal_type = None
        if row["signal_change"] > 0:  # Bullish crossover
            signal_type = "buy"
        elif row["signal_change"] < 0:  # Bearish crossover
            signal_type = "sell"

        if signal_type:
            return {
                "type": signal_type,
                "price": row["close"],
                "timestamp": row.name if isinstance(row.name, datetime) else None,
                "take_profit": row["close"] * (1 + self.params.take_profit_pct / 100)
                if signal_type == "buy"
                else row["close"] * (1 - self.params.take_profit_pct / 100),
                "stop_loss": row["close"] * (1 - self.params.stop_loss_pct / 100)
                if signal_type == "buy"
                else row["close"] * (1 + self.params.stop_loss_pct / 100),
            }

        return None

    def should_exit_position(self, data: pd.DataFrame, index: int) -> Tuple[bool, str]:
        """
        Check if current position should be exited based on strategy rules.

        Args:
            data: Market data DataFrame
            index: Current index in DataFrame

        Returns:
            Tuple of (should_exit, reason)
        """
        if not self.current_position:
            return False, "No position"

        row = data.iloc[index]
        position_type = self.current_position["type"]
        entry_price = self.current_position["price"]

        # Check stop loss
        if position_type == "buy":
            if row["low"] <= self.current_position["stop_loss"]:
                return True, "Stop loss hit"
            if row["high"] >= self.current_position["take_profit"]:
                return True, "Take profit hit"
        else:  # sell position
            if row["high"] >= self.current_position["stop_loss"]:
                return True, "Stop loss hit"
            if row["low"] <= self.current_position["take_profit"]:
                return True, "Take profit hit"

        # Check for opposing signals
        if (position_type == "buy" and row["signal"] == -1) or (
            position_type == "sell" and row["signal"] == 1
        ):
            return True, "Signal reversal"

        return False, "Hold position"

    def update_position(self, position: Optional[Dict] = None):
        """
        Update the current position tracker.

        Args:
            position: New position details or None to clear position
        """
        self.current_position = position

    def optimize_parameters(
        self, data: pd.DataFrame, parameter_ranges: Dict[str, List[float]]
    ) -> Dict[str, float]:
        """
        Optimize strategy parameters using historical data.

        Args:
            data: Historical market data
            parameter_ranges: Dictionary of parameters and their possible values

        Returns:
            Dictionary of optimized parameters
        """
        # Implementation for parameter optimization
        # This would typically use a grid search or genetic algorithm approach
        # Returns the best performing parameter combination
        # For now, return default parameters
        return {
            "short_ema_period": self.params.short_ema_period,
            "long_ema_period": self.params.long_ema_period,
            "take_profit_pct": self.params.take_profit_pct,
            "stop_loss_pct": self.params.stop_loss_pct,
            "position_size_pct": self.params.position_size_pct,
        }
