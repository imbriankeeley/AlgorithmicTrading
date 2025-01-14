from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from ..core.database import Base


class TradeStatus(PyEnum):
    """Enumeration of possible trade statuses."""

    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TradeType(PyEnum):
    """Enumeration of possible trade types."""

    BUY = "buy"
    SELL = "sell"


class Trade(Base):
    """
    SQLAlchemy model for trading operations.
    Tracks individual trades including entry, exit, and performance metrics.
    """

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=True)

    # Trade Details
    type = Column(String, nullable=False)  # buy/sell
    status = Column(String, nullable=False, default=TradeStatus.PENDING.value)
    symbol = Column(String, nullable=False)

    # Entry Details
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    size = Column(Float, nullable=False)  # Position size in base currency

    # Exit Details
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)

    # Risk Management
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)

    # Performance Metrics
    realized_pnl = Column(Float, nullable=True)
    fees = Column(Float, nullable=True, default=0.0)

    # Strategy Information
    strategy_name = Column(String, nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    signal = relationship("Signal", back_populates="trades")

    # Additional Metadata
    notes = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def duration(self) -> Optional[float]:
        """Calculate the duration of the trade in seconds."""
        if self.exit_time and self.entry_time:
            return (self.exit_time - self.entry_time).total_seconds()
        return None

    @property
    def is_active(self) -> bool:
        """Check if the trade is currently active."""
        return self.status in [TradeStatus.PENDING.value, TradeStatus.OPEN.value]

    @property
    def current_pnl(self) -> Optional[float]:
        """Calculate current PnL if trade is closed."""
        if self.realized_pnl is not None:
            return self.realized_pnl - (self.fees or 0)
        return None

    @property
    def roi_percentage(self) -> Optional[float]:
        """Calculate ROI as a percentage."""
        if self.realized_pnl is not None and self.entry_price and self.size:
            investment = self.entry_price * self.size
            if investment > 0:
                return (self.realized_pnl / investment) * 100
        return None

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized PnL based on current market price.

        Args:
            current_price: Current market price of the asset

        Returns:
            Unrealized profit/loss in quote currency
        """
        if not self.is_active:
            return self.realized_pnl if self.realized_pnl is not None else 0.0

        price_diff = current_price - self.entry_price
        if self.type == TradeType.SELL.value:
            price_diff = -price_diff

        return price_diff * self.size - (self.fees or 0)

    def update_status(
        self, new_status: TradeStatus, error_message: Optional[str] = None
    ):
        """
        Update trade status and optionally set error message.

        Args:
            new_status: New status to set
            error_message: Optional error message for failed trades
        """
        self.status = new_status.value
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def close_trade(self, exit_price: float, exit_time: Optional[datetime] = None):
        """
        Close the trade with given exit details.

        Args:
            exit_price: Exit price of the trade
            exit_time: Optional exit timestamp (defaults to current UTC time)
        """
        self.exit_price = exit_price
        self.exit_time = exit_time or datetime.utcnow()
        self.status = TradeStatus.CLOSED.value

        # Calculate realized PnL
        price_diff = exit_price - self.entry_price
        if self.type == TradeType.SELL.value:
            price_diff = -price_diff

        self.realized_pnl = price_diff * self.size - (self.fees or 0)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert trade instance to dictionary representation."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "type": self.type,
            "status": self.status,
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "size": self.size,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "realized_pnl": self.realized_pnl,
            "fees": self.fees,
            "strategy_name": self.strategy_name,
            "duration": self.duration,
            "roi_percentage": self.roi_percentage,
            "notes": self.notes,
            "error_message": self.error_message,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
