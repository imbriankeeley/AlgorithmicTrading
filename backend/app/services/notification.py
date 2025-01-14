from typing import Optional, List, Dict
import logging
from datetime import datetime, timedelta
from enum import Enum
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException

from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Enumeration for notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """
    SMS notification service using Twilio.
    Handles sending trading alerts and system notifications with rate limiting
    and priority-based message queuing.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        rate_limit: int = 10,  # Maximum messages per minute
        cooldown_period: int = 300,  # 5 minutes between similar notifications
    ):
        """
        Initialize the notification service.

        Args:
            account_sid: Twilio account SID (falls back to env vars)
            auth_token: Twilio auth token (falls back to env vars)
            from_number: Twilio phone number (falls back to env vars)
            rate_limit: Maximum messages per minute
            cooldown_period: Seconds to wait before sending similar notifications
        """
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_FROM_NUMBER

        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to initialize notification service"
            )

        self.rate_limit = rate_limit
        self.cooldown_period = cooldown_period

        # Track message history for rate limiting
        self.message_history: List[datetime] = []
        self.notification_cache: Dict[str, datetime] = {}

    def _check_rate_limit(self) -> bool:
        """
        Check if sending a message would exceed the rate limit.

        Returns:
            Boolean indicating if message can be sent
        """
        current_time = datetime.now()
        # Remove messages older than 1 minute from history
        self.message_history = [
            time
            for time in self.message_history
            if time > current_time - timedelta(minutes=1)
        ]
        return len(self.message_history) < self.rate_limit

    def _check_cooldown(self, message_key: str) -> bool:
        """
        Check if similar message is in cooldown period.

        Args:
            message_key: Unique identifier for message type

        Returns:
            Boolean indicating if message can be sent
        """
        if message_key in self.notification_cache:
            last_sent = self.notification_cache[message_key]
            if datetime.now() - last_sent < timedelta(seconds=self.cooldown_period):
                return False
        return True

    def _format_trade_alert(
        self,
        trade_type: str,
        symbol: str,
        price: float,
        size: float,
        pnl: Optional[float] = None,
    ) -> str:
        """
        Format trade alert message.

        Args:
            trade_type: Type of trade (entry, exit, etc.)
            symbol: Trading pair symbol
            price: Trade price
            size: Trade size
            pnl: Optional profit/loss amount

        Returns:
            Formatted message string
        """
        message = f"TRADE ALERT: {trade_type.upper()} "
        message += f"{symbol} @ ${price:,.2f} "
        message += f"Size: {size:,.8f}"

        if pnl is not None:
            message += f" PnL: ${pnl:,.2f}"

        return message

    async def send_notification(
        self,
        to_number: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        message_key: Optional[str] = None,
    ) -> bool:
        """
        Send SMS notification with rate limiting and priority handling.

        Args:
            to_number: Recipient phone number
            message: Message content
            priority: Message priority level
            message_key: Optional key for cooldown tracking

        Returns:
            Boolean indicating if message was sent successfully
        """
        try:
            # Check rate limit unless CRITICAL priority
            if (
                priority != NotificationPriority.CRITICAL
                and not self._check_rate_limit()
            ):
                logger.warning("Rate limit exceeded, skipping notification")
                return False

            # Check cooldown for similar messages
            if (
                message_key
                and priority != NotificationPriority.CRITICAL
                and not self._check_cooldown(message_key)
            ):
                logger.debug(f"Message {message_key} in cooldown period")
                return False

            # Send message via Twilio
            message = await self._send_sms(to_number, message)

            # Update tracking
            self.message_history.append(datetime.now())
            if message_key:
                self.notification_cache[message_key] = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            if priority == NotificationPriority.CRITICAL:
                raise HTTPException(
                    status_code=500, detail="Failed to send critical notification"
                )
            return False

    async def _send_sms(self, to_number: str, message: str) -> dict:
        """
        Send SMS using Twilio API.

        Args:
            to_number: Recipient phone number
            message: Message content

        Returns:
            Twilio message response

        Raises:
            HTTPException: If sending fails
        """
        try:
            message = await self.client.messages.create(
                body=message, from_=self.from_number, to=to_number
            )
            logger.info(f"Sent SMS notification: {message.sid}")
            return message

        except TwilioRestException as e:
            logger.error(f"Twilio API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

    async def notify_trade_entry(
        self, to_number: str, symbol: str, price: float, size: float
    ) -> bool:
        """
        Send trade entry notification.

        Args:
            to_number: Recipient phone number
            symbol: Trading pair symbol
            price: Entry price
            size: Position size

        Returns:
            Boolean indicating if notification was sent
        """
        message = self._format_trade_alert("ENTRY", symbol, price, size)
        message_key = f"trade_entry_{symbol}"
        return await self.send_notification(
            to_number, message, NotificationPriority.HIGH, message_key
        )

    async def notify_trade_exit(
        self,
        to_number: str,
        symbol: str,
        price: float,
        size: float,
        pnl: float,
        exit_reason: str,
    ) -> bool:
        """
        Send trade exit notification.

        Args:
            to_number: Recipient phone number
            symbol: Trading pair symbol
            price: Exit price
            size: Position size
            pnl: Realized profit/loss
            exit_reason: Reason for exit

        Returns:
            Boolean indicating if notification was sent
        """
        message = self._format_trade_alert("EXIT", symbol, price, size, pnl)
        message += f"\nReason: {exit_reason}"
        message_key = f"trade_exit_{symbol}"
        return await self.send_notification(
            to_number, message, NotificationPriority.HIGH, message_key
        )

    async def notify_error(
        self,
        to_number: str,
        error_message: str,
        priority: NotificationPriority = NotificationPriority.HIGH,
    ) -> bool:
        """
        Send error notification.

        Args:
            to_number: Recipient phone number
            error_message: Error details
            priority: Message priority level

        Returns:
            Boolean indicating if notification was sent
        """
        message = f"ERROR ALERT: {error_message}"
        return await self.send_notification(to_number, message, priority)

    async def notify_risk_alert(
        self,
        to_number: str,
        alert_type: str,
        details: str,
        priority: NotificationPriority = NotificationPriority.HIGH,
    ) -> bool:
        """
        Send risk management alert.

        Args:
            to_number: Recipient phone number
            alert_type: Type of risk alert
            details: Alert details
            priority: Message priority level

        Returns:
            Boolean indicating if notification was sent
        """
        message = f"RISK ALERT: {alert_type}\n{details}"
        message_key = f"risk_{alert_type.lower()}"
        return await self.send_notification(to_number, message, priority, message_key)

    async def notify_system_status(
        self,
        to_number: str,
        status: str,
        details: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> bool:
        """
        Send system status notification.

        Args:
            to_number: Recipient phone number
            status: System status message
            details: Optional additional details
            priority: Message priority level

        Returns:
            Boolean indicating if notification was sent
        """
        message = f"SYSTEM STATUS: {status}"
        if details:
            message += f"\n{details}"
        message_key = f"system_{status.lower()}"
        return await self.send_notification(to_number, message, priority, message_key)
