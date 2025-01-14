from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from ....core.trading.bot import TradingBot
from ....core.trading.strategy import MomentumStrategy, StrategyParameters
from ....core.trading.risk_manager import RiskManager, RiskParameters
from ....core.exchange.coinbase import CoinbaseClient
from ....models.trade import Trade
from ....schemas.trade import (
    TradeCreate,
    TradeUpdate,
    TradeResponse,
    TradingSessionConfig,
    TradingStatus,
    StrategyConfig,
)
from ....services.database import get_db
from ....dependencies import get_current_user, get_trading_bot

router = APIRouter()


@router.post("/session/start", response_model=TradingStatus)
async def start_trading_session(
    config: TradingSessionConfig,
    background_tasks: BackgroundTasks,
    bot: TradingBot = Depends(get_trading_bot),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Start a new trading session with specified configuration.

    Args:
        config: Trading session configuration parameters
        background_tasks: FastAPI background tasks
        bot: Trading bot instance
        db: Database session
        current_user: Authenticated user information
    """
    try:
        # Initialize strategy with provided parameters
        strategy_params = StrategyParameters(
            short_ema_period=config.strategy_params.short_ema_period,
            long_ema_period=config.strategy_params.long_ema_period,
            take_profit_pct=config.strategy_params.take_profit_pct,
            stop_loss_pct=config.strategy_params.stop_loss_pct,
            position_size_pct=config.strategy_params.position_size_pct,
        )

        # Initialize risk parameters
        risk_params = RiskParameters(
            max_position_size=config.risk_params.max_position_size,
            max_daily_drawdown=config.risk_params.max_daily_drawdown,
            max_trades_per_day=config.risk_params.max_trades_per_day,
        )

        # Configure and start the trading bot
        bot.configure(
            strategy_params=strategy_params,
            risk_params=risk_params,
            trading_pairs=config.trading_pairs,
        )

        # Start trading in background task
        background_tasks.add_task(bot.start_trading)

        return {"status": "started", "timestamp": datetime.utcnow()}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start trading session: {str(e)}"
        )


@router.post("/session/stop", response_model=TradingStatus)
async def stop_trading_session(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Stop the current trading session."""
    try:
        await bot.stop_trading()
        return {"status": "stopped", "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop trading session: {str(e)}"
        )


@router.get("/session/status", response_model=TradingStatus)
async def get_trading_status(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Get current trading session status."""
    return {
        "status": bot.status,
        "timestamp": datetime.utcnow(),
        "active_since": bot.started_at,
        "total_trades": bot.total_trades,
        "active_trades": len(bot.active_trades),
    }


@router.put("/strategy/config", response_model=StrategyConfig)
async def update_strategy_config(
    config: StrategyConfig,
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Update trading strategy configuration."""
    try:
        new_params = StrategyParameters(**config.dict())
        bot.update_strategy_parameters(new_params)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update strategy configuration: {str(e)}"
        )


@router.get("/trades/active", response_model=List[TradeResponse])
async def get_active_trades(
    bot: TradingBot = Depends(get_trading_bot),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all currently active trades."""
    try:
        active_trades = bot.get_active_trades()
        return [TradeResponse.from_orm(trade) for trade in active_trades]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch active trades: {str(e)}"
        )


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade_details(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get details for a specific trade."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeResponse.from_orm(trade)


@router.post("/trades/{trade_id}/close")
async def close_trade(
    trade_id: int,
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Manually close a specific trade."""
    try:
        await bot.close_trade(trade_id)
        return {"status": "success", "message": f"Trade {trade_id} closed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close trade: {str(e)}")


@router.get("/performance/metrics")
async def get_performance_metrics(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Get current trading performance metrics."""
    try:
        metrics = bot.get_performance_metrics()
        return {
            "total_profit_loss": metrics.total_pnl,
            "win_rate": metrics.win_rate,
            "average_profit": metrics.avg_profit,
            "average_loss": metrics.avg_loss,
            "largest_profit": metrics.max_profit,
            "largest_loss": metrics.max_loss,
            "total_trades": metrics.total_trades,
            "successful_trades": metrics.successful_trades,
            "failed_trades": metrics.failed_trades,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch performance metrics: {str(e)}"
        )


@router.get("/risk/metrics")
async def get_risk_metrics(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Get current risk metrics."""
    try:
        risk_metrics = bot.risk_manager.get_risk_metrics()
        return risk_metrics
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch risk metrics: {str(e)}"
        )


@router.post("/emergency/stop")
async def emergency_stop(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """Emergency stop all trading activities."""
    try:
        await bot.emergency_stop()
        return {
            "status": "stopped",
            "message": "Emergency stop executed successfully",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute emergency stop: {str(e)}"
        )
