from typing import Optional, Dict, List, Any, AsyncGenerator
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from functools import wraps

from fastapi import Depends, HTTPException
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy Base
Base = declarative_base()


class DatabaseService:
    """
    Database service handling Supabase interactions and connection management.
    Implements connection pooling, retry logic, and transaction management.
    """

    def __init__(self):
        """Initialize database connections and connection pools."""
        try:
            # Initialize Supabase client
            self.supabase: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
                options=ClientOptions(
                    schema="public",
                    headers={"x-application-name": "crypto-trading-bot"},
                    postgrest_client_timeout=10,  # 10 second timeout
                ),
            )

            # Initialize SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True,
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            logger.info("Database service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database service: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Database initialization failed"
            )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Session, None]:
        """
        Get database session with automatic cleanup.

        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    async def execute_with_retry(
        self, operation: str, query: Any, params: Dict = None, max_retries: int = 3
    ) -> Any:
        """
        Execute database operation with retry logic.

        Args:
            operation: Operation description for logging
            query: Query to execute
            params: Query parameters
            max_retries: Maximum retry attempts

        Returns:
            Query results

        Raises:
            HTTPException: If operation fails after retries
        """
        attempt = 0
        last_error = None

        while attempt < max_retries:
            try:
                result = (
                    await self.supabase.rpc(query, params)
                    if params
                    else await self.supabase.rpc(query)
                )
                return result
            except Exception as e:
                attempt += 1
                last_error = e
                logger.warning(
                    f"Database operation '{operation}' failed (attempt {attempt}): {str(e)}"
                )
                if attempt == max_retries:
                    logger.error(
                        f"Database operation '{operation}' failed after {max_retries} attempts: {str(e)}"
                    )
                    raise HTTPException(
                        status_code=500, detail=f"Database operation failed: {str(e)}"
                    )

    # Trade-related operations

    async def create_trade(self, trade_data: Dict) -> Dict:
        """Create new trade record."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("trades").insert(trade_data).execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create trade: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create trade")

    async def update_trade(self, trade_id: int, trade_data: Dict) -> Dict:
        """Update existing trade record."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("trades")
                    .update(trade_data)
                    .eq("id", trade_id)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update trade {trade_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update trade")

    async def get_trade(self, trade_id: int) -> Optional[Dict]:
        """Get trade by ID."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("trades")
                    .select("*")
                    .eq("id", trade_id)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get trade {trade_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch trade")

    async def get_trades(
        self,
        user_id: int,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get trades with optional filters."""
        try:
            query = self.supabase.table("trades").select("*")

            # Apply filters
            query = query.eq("user_id", user_id)
            if status:
                query = query.eq("status", status)
            if symbol:
                query = query.eq("symbol", symbol)
            if start_date:
                query = query.gte("entry_time", start_date.isoformat())
            if end_date:
                query = query.lte("entry_time", end_date.isoformat())

            # Apply pagination
            result = (
                await query.range(offset, offset + limit - 1)
                .order("entry_time", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to fetch trades: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch trades")

    # Backtest-related operations

    async def create_backtest(self, backtest_data: Dict) -> Dict:
        """Create new backtest record."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("backtests")
                    .insert(backtest_data)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to create backtest: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create backtest")

    async def get_backtest(self, backtest_id: int) -> Optional[Dict]:
        """Get backtest by ID."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("backtests")
                    .select("*")
                    .eq("id", backtest_id)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get backtest {backtest_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch backtest")

    async def get_backtests(
        self,
        user_id: int,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get backtests with optional filters."""
        try:
            query = self.supabase.table("backtests").select("*")

            # Apply filters
            query = query.eq("user_id", user_id)
            if symbol:
                query = query.eq("symbol", symbol)
            if start_date:
                query = query.gte("start_date", start_date.isoformat())
            if end_date:
                query = query.lte("end_date", end_date.isoformat())

            # Apply pagination
            result = (
                await query.range(offset, offset + limit - 1)
                .order("execution_time", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Failed to fetch backtests: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch backtests")

    # User-related operations

    async def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """Get user settings."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("user_settings")
                    .select("*")
                    .eq("user_id", user_id)
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get user settings for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch user settings")

    async def update_user_settings(self, user_id: int, settings: Dict) -> Dict:
        """Update user settings."""
        try:
            async with self.get_session() as session:
                result = (
                    await self.supabase.table("user_settings")
                    .upsert(
                        {
                            "user_id": user_id,
                            **settings,
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                    )
                    .execute()
                )
                return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to update settings for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to update user settings"
            )


# Database dependency
db_service = DatabaseService()


def get_db() -> DatabaseService:
    """FastAPI dependency for database service."""
    return db_service
