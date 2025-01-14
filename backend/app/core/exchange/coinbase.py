from typing import Dict, List, Optional, Tuple
import json
import hmac
import hashlib
import time
from base64 import b64encode
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel
import pandas as pd
from ...config import settings


class OrderRequest(BaseModel):
    """Model for order placement requests."""

    symbol: str
    side: str  # buy or sell
    type: str  # market or limit
    size: float
    price: Optional[float] = None
    time_in_force: str = "IOC"  # IOC, GTT, GTC
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None


class CoinbaseClient:
    """
    Coinbase Advanced API client handling market data, trading, and account operations.
    Implements rate limiting, authentication, and error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = "https://api.coinbase.com/api/v3",
    ):
        """
        Initialize the Coinbase client.

        Args:
            api_key: Coinbase API key (optional, falls back to env vars)
            api_secret: Coinbase API secret (optional, falls back to env vars)
            base_url: Base URL for API requests
        """
        self.api_key = api_key or settings.COINBASE_API_KEY
        self.api_secret = api_secret or settings.COINBASE_API_SECRET
        self.base_url = base_url
        self.session = httpx.Client(timeout=30.0)
        self.last_request_time = 0
        self.rate_limit_per_second = 10

    def _generate_signature(
        self, timestamp: str, method: str, path: str, body: str = ""
    ) -> str:
        """
        Generate signature for API authentication.

        Args:
            timestamp: Unix timestamp
            method: HTTP method
            path: Request path
            body: Request body (if any)

        Returns:
            Base64 encoded signature
        """
        message = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        )
        return b64encode(signature.digest()).decode("utf-8")

    def _headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """
        Create headers for authenticated requests.

        Args:
            method: HTTP method
            path: Request path
            body: Request body (if any)

        Returns:
            Dictionary of request headers
        """
        timestamp = str(int(time.time()))
        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-SIGN": self._generate_signature(timestamp, method, path, body),
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict:
        """
        Make an authenticated API request with rate limiting.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            API response data

        Raises:
            httpx.HTTPError: If the request fails
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 1.0 / self.rate_limit_per_second:
            time.sleep(1.0 / self.rate_limit_per_second - time_since_last_request)

        url = f"{self.base_url}{endpoint}"
        body = json.dumps(data) if data else ""
        headers = self._headers(method, endpoint, body)

        try:
            response = await self.session.request(
                method, url, headers=headers, params=params, json=data, timeout=30.0
            )
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json()
        except httpx.HTTPError as e:
            # Log the error and re-raise
            print(f"Coinbase API error: {str(e)}")
            raise

    async def get_market_data(
        self, symbol: str, interval: str = "1m", limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical market data.

        Args:
            symbol: Trading pair symbol
            interval: Candle interval (1m, 5m, 15m, 1h, etc.)
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        endpoint = f"/products/{symbol}/candles"
        params = {"granularity": interval, "limit": limit}

        response = await self._make_request("GET", endpoint, params=params)

        df = pd.DataFrame(
            response, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df.set_index("timestamp", inplace=True)
        return df

    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker information.

        Args:
            symbol: Trading pair symbol

        Returns:
            Dictionary with current price and 24h stats
        """
        endpoint = f"/products/{symbol}/ticker"
        return await self._make_request("GET", endpoint)

    async def get_order_book(self, symbol: str, level: int = 2) -> Dict:
        """
        Get order book data.

        Args:
            symbol: Trading pair symbol
            level: Order book level (1, 2, or 3)

        Returns:
            Dictionary with order book data
        """
        endpoint = f"/products/{symbol}/book"
        params = {"level": level}
        return await self._make_request("GET", endpoint, params=params)

    async def get_account_balance(self) -> List[Dict]:
        """
        Get account balances.

        Returns:
            List of dictionaries with account balances
        """
        endpoint = "/accounts"
        return await self._make_request("GET", endpoint)

    async def create_order(self, order: OrderRequest) -> Dict:
        """
        Place a new order.

        Args:
            order: Order request model

        Returns:
            Dictionary with order details
        """
        endpoint = "/orders"
        order_data = order.dict(exclude_none=True)
        return await self._make_request("POST", endpoint, data=order_data)

    async def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel

        Returns:
            Dictionary with cancellation details
        """
        endpoint = f"/orders/{order_id}"
        return await self._make_request("DELETE", endpoint)

    async def get_order(self, order_id: str) -> Dict:
        """
        Get details of a specific order.

        Args:
            order_id: Order ID to fetch

        Returns:
            Dictionary with order details
        """
        endpoint = f"/orders/{order_id}"
        return await self._make_request("GET", endpoint)

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get list of open orders.

        Args:
            symbol: Optional symbol to filter by

        Returns:
            List of dictionaries with order details
        """
        endpoint = "/orders"
        params = {"status": "open"}
        if symbol:
            params["product_id"] = symbol
        return await self._make_request("GET", endpoint, params=params)

    async def get_fills(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get list of filled orders.

        Args:
            symbol: Optional symbol to filter by
            order_id: Optional order ID to filter by
            limit: Number of fills to fetch

        Returns:
            List of dictionaries with fill details
        """
        endpoint = "/fills"
        params = {"limit": limit}
        if symbol:
            params["product_id"] = symbol
        if order_id:
            params["order_id"] = order_id
        return await self._make_request("GET", endpoint, params=params)

    def get_market_volatility(self, symbol: str = "BTC-USD", window: int = 24) -> float:
        """
        Calculate market volatility over specified window.

        Args:
            symbol: Trading pair symbol
            window: Time window in hours

        Returns:
            Annualized volatility percentage
        """
        # Fetch hourly data for the specified window
        df = await self.get_market_data(symbol, interval="1h", limit=window)

        # Calculate returns and annualized volatility
        returns = df["close"].pct_change().dropna()
        volatility = returns.std() * (365 * 24) ** 0.5 * 100

        return volatility

    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
