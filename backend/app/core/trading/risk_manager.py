from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import numpy as np
from ..exchange.coinbase import (
    CoinbaseClient,
)  # Assuming this exists based on project structure


@dataclass
class RiskParameters:
    """Risk management parameters configuration."""

    max_position_size: float = 1000.0  # Maximum position size in USD
    max_daily_drawdown: float = 5.0  # Maximum daily drawdown percentage
    max_trades_per_day: int = 10  # Maximum number of trades per day
    max_concurrent_trades: int = 2  # Maximum number of concurrent open positions
    min_trade_size: float = 10.0  # Minimum trade size in USD
    max_leverage: float = 1.0  # Maximum allowed leverage (1.0 = no leverage)
    emergency_stop_loss: float = 15.0  # Emergency stop loss percentage
    volatility_threshold: float = 30.0  # Maximum allowed volatility (annualized %)


class RiskManager:
    """
    Manages trading risk through position sizing, exposure limits,
    and trading frequency controls.
    """

    def __init__(
        self,
        parameters: Optional[RiskParameters] = None,
        exchange_client: Optional[CoinbaseClient] = None,
    ):
        """
        Initialize the risk manager with configurable parameters.

        Args:
            parameters: Risk management configuration parameters
            exchange_client: Exchange client for market data and account info
        """
        self.params = parameters or RiskParameters()
        self.exchange_client = exchange_client
        self.trade_history: List[Dict] = []
        self.open_positions: Dict[str, Dict] = {}
        self.daily_pnl = 0.0
        self.last_reset = datetime.now()

    def reset_daily_metrics(self):
        """Reset daily tracking metrics."""
        if datetime.now() - self.last_reset > timedelta(days=1):
            self.daily_pnl = 0.0
            self.trade_history = [
                trade
                for trade in self.trade_history
                if trade["timestamp"] > datetime.now() - timedelta(days=1)
            ]
            self.last_reset = datetime.now()

    def calculate_position_size(
        self, capital: float, price: float, volatility: float
    ) -> float:
        """
        Calculate safe position size based on capital and market conditions.

        Args:
            capital: Available trading capital
            price: Current asset price
            volatility: Current market volatility (annualized %)

        Returns:
            Recommended position size in USD
        """
        # Adjust position size based on volatility
        volatility_scalar = max(
            0.2, 1 - (volatility / self.params.volatility_threshold)
        )

        # Base position size on capital and volatility
        base_size = (
            min(
                capital * 0.01,  # 1% of capital
                self.params.max_position_size,
            )
            * volatility_scalar
        )

        # Ensure minimum trade size
        if base_size < self.params.min_trade_size:
            return 0.0  # Don't trade if below minimum size

        return min(base_size, self.params.max_position_size)

    def validate_trade(
        self,
        trade_type: str,
        size: float,
        price: float,
        stop_loss: float,
        take_profit: float,
    ) -> Tuple[bool, str]:
        """
        Validate trade parameters against risk rules.

        Args:
            trade_type: Type of trade ('buy' or 'sell')
            size: Trade size in USD
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Tuple of (is_valid, reason)
        """
        self.reset_daily_metrics()

        # Check trade frequency
        if len(self.trade_history) >= self.params.max_trades_per_day:
            return False, "Maximum daily trades exceeded"

        # Check concurrent positions
        if len(self.open_positions) >= self.params.max_concurrent_trades:
            return False, "Maximum concurrent positions reached"

        # Validate position size
        if size > self.params.max_position_size:
            return False, "Position size exceeds maximum allowed"
        if size < self.params.min_trade_size:
            return False, "Position size below minimum allowed"

        # Validate stop loss
        stop_loss_pct = abs((stop_loss - price) / price * 100)
        if stop_loss_pct > self.params.emergency_stop_loss:
            return False, "Stop loss exceeds maximum allowed"

        # Validate risk/reward ratio
        risk = abs(price - stop_loss)
        reward = abs(take_profit - price)
        if risk > 0 and reward / risk < 1.5:  # Minimum 1.5:1 reward/risk ratio
            return False, "Insufficient risk/reward ratio"

        return True, "Trade validated"

    def update_position(self, trade_id: str, position_update: Dict) -> None:
        """
        Update tracking for an open position.

        Args:
            trade_id: Unique trade identifier
            position_update: Dictionary with position details
        """
        if position_update.get("status") == "closed":
            if trade_id in self.open_positions:
                # Update daily P&L
                self.daily_pnl += position_update.get("realized_pnl", 0)
                del self.open_positions[trade_id]
        else:
            self.open_positions[trade_id] = position_update

        # Add to trade history
        self.trade_history.append(
            {"trade_id": trade_id, "timestamp": datetime.now(), **position_update}
        )

    def check_risk_limits(self) -> Tuple[bool, str]:
        """
        Check if any risk limits have been breached.

        Returns:
            Tuple of (is_safe, reason)
        """
        self.reset_daily_metrics()

        # Check daily drawdown
        if abs(self.daily_pnl) > self.params.max_daily_drawdown:
            return False, "Daily drawdown limit exceeded"

        # Check total exposure
        total_exposure = sum(
            pos.get("size", 0) * pos.get("price", 0)
            for pos in self.open_positions.values()
        )
        if total_exposure > self.params.max_position_size:
            return False, "Total exposure limit exceeded"

        # Check market volatility if exchange client is available
        if self.exchange_client:
            try:
                volatility = self.exchange_client.get_market_volatility()
                if volatility > self.params.volatility_threshold:
                    return False, "Market volatility too high"
            except Exception as e:
                # Log the error but continue with other checks
                print(f"Error checking market volatility: {e}")

        return True, "Within risk limits"

    def get_risk_metrics(self) -> Dict:
        """
        Get current risk metrics and limits status.

        Returns:
            Dictionary of current risk metrics
        """
        self.reset_daily_metrics()

        total_exposure = sum(
            pos.get("size", 0) * pos.get("price", 0)
            for pos in self.open_positions.values()
        )

        return {
            "daily_pnl": self.daily_pnl,
            "open_positions": len(self.open_positions),
            "daily_trades": len(self.trade_history),
            "total_exposure": total_exposure,
            "exposure_limit_remaining": self.params.max_position_size - total_exposure,
            "trades_remaining_today": self.params.max_trades_per_day
            - len(self.trade_history),
        }
