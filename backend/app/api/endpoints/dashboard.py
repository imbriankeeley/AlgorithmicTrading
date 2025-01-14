from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd

from ....core.trading.bot import TradingBot
from ....core.backtesting.data_processor import HistoricalDataProcessor
from ....models.trade import Trade
from ....services.database import get_db
from ....dependencies import get_current_user, get_trading_bot

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    bot: TradingBot = Depends(get_trading_bot),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get summary statistics for the dashboard overview.
    Includes key metrics like total profit/loss, active trades, and system status.
    """
    try:
        # Get performance metrics
        performance = bot.get_performance_metrics()
        risk_metrics = bot.risk_manager.get_risk_metrics()
        
        # Get recent trades
        recent_trades = (
            db.query(Trade)
            .filter(Trade.entry_time >= datetime.utcnow() - timedelta(days=7))
            .order_by(Trade.entry_time.desc())
            .limit(5)
            .all()
        )

        return {
            "total_pnl": performance.total_pnl,
            "daily_pnl": performance.daily_pnl,
            "win_rate": performance.win_rate,
            "total_trades": performance.total_trades,
            "active_trades": len(bot.active_trades),
            "available_capital": risk_metrics["exposure_limit_remaining"],
            "system_status": bot.status,
            "recent_trades": [trade.to_dict() for trade in recent_trades],
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard summary: {str(e)}"
        )

@router.get("/performance")
async def get_performance_metrics(
    timeframe: str = "1d",
    bot: TradingBot = Depends(get_trading_bot),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed performance metrics for specified timeframe.
    Timeframe options: 1d, 1w, 1m, 3m, 6m, 1y, all
    """
    try:
        # Calculate timeframe start date
        timeframe_map = {
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
        }
        
        start_date = (
            datetime.utcnow() - timeframe_map[timeframe]
            if timeframe in timeframe_map
            else None
        )

        # Query trades for the period
        query = db.query(Trade)
        if start_date:
            query = query.filter(Trade.entry_time >= start_date)
        trades = query.order_by(Trade.entry_time.asc()).all()

        # Calculate metrics
        total_trades = len(trades)
        profitable_trades = sum(1 for t in trades if t.realized_pnl and t.realized_pnl > 0)
        
        return {
            "summary": {
                "total_trades": total_trades,
                "profitable_trades": profitable_trades,
                "win_rate": profitable_trades / total_trades if total_trades > 0 else 0,
                "total_pnl": sum(t.realized_pnl or 0 for t in trades),
                "largest_win": max((t.realized_pnl or 0) for t in trades),
                "largest_loss": min((t.realized_pnl or 0) for t in trades),
                "average_trade_duration": sum(
                    (t.duration or 0) for t in trades
                ) / total_trades if total_trades > 0 else 0,
            },
            "daily_pnl": _calculate_daily_pnl(trades),
            "trade_distribution": _calculate_trade_distribution(trades),
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": datetime.utcnow(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance metrics: {str(e)}"
        )

@router.get("/portfolio")
async def get_portfolio_status(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current portfolio status including positions and asset allocation.
    """
    try:
        active_positions = bot.get_active_trades()
        risk_metrics = bot.risk_manager.get_risk_metrics()
        
        return {
            "total_equity": bot.get_total_equity(),
            "available_capital": risk_metrics["exposure_limit_remaining"],
            "active_positions": [
                {
                    "symbol": pos.symbol,
                    "type": pos.type,
                    "size": pos.size,
                    "entry_price": pos.entry_price,
                    "current_price": bot.get_current_price(pos.symbol),
                    "unrealized_pnl": pos.calculate_unrealized_pnl(
                        bot.get_current_price(pos.symbol)
                    ),
                    "entry_time": pos.entry_time,
                }
                for pos in active_positions
            ],
            "allocation": {
                "used": risk_metrics["total_exposure"],
                "available": risk_metrics["exposure_limit_remaining"],
                "reserved": risk_metrics.get("reserved_capital", 0),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch portfolio status: {str(e)}"
        )

@router.get("/risk-metrics")
async def get_risk_analysis(
    bot: TradingBot = Depends(get_trading_bot),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed risk analysis and exposure metrics.
    """
    try:
        risk_metrics = bot.risk_manager.get_risk_metrics()
        
        # Get historical drawdown data
        trades = (
            db.query(Trade)
            .filter(Trade.exit_time >= datetime.utcnow() - timedelta(days=30))
            .order_by(Trade.entry_time.asc())
            .all()
        )
        
        return {
            "current_exposure": {
                "total": risk_metrics["total_exposure"],
                "per_asset": _calculate_exposure_per_asset(bot.active_trades),
                "limit_remaining": risk_metrics["exposure_limit_remaining"],
            },
            "drawdown_analysis": {
                "current_drawdown": _calculate_current_drawdown(trades),
                "max_drawdown": _calculate_max_drawdown(trades),
                "average_drawdown": _calculate_average_drawdown(trades),
                "drawdown_periods": _identify_drawdown_periods(trades),
            },
            "risk_limits": {
                "max_position_size": bot.risk_manager.params.max_position_size,
                "max_daily_drawdown": bot.risk_manager.params.max_daily_drawdown,
                "max_trades_per_day": bot.risk_manager.params.max_trades_per_day,
                "trades_remaining_today": risk_metrics["trades_remaining_today"],
            },
            "volatility_metrics": _calculate_volatility_metrics(bot),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch risk analysis: {str(e)}"
        )

@router.get("/system-status")
async def get_system_status(
    bot: TradingBot = Depends(get_trading_bot),
    current_user: dict = Depends(get_current_user),
):
    """
    Get system health and operational metrics.
    """
    try:
        return {
            "trading_status": {
                "status": bot.status,
                "active_since": bot.started_at,
                "last_trade_time": bot.last_trade_time,
                "error_count": bot.error_count,
            },
            "performance_metrics": {
                "api_latency": bot.get_api_latency(),
                "order_success_rate": bot.get_order_success_rate(),
                "system_load": _get_system_load(),
            },
            "exchange_status": {
                "connected": bot.is_exchange_connected(),
                "rate_limits": bot.get_rate_limit_status(),
                "trading_enabled": bot.is_trading_enabled(),
            },
            "maintenance": {
                "last_error": bot.last_error,
                "last_maintenance": bot.last_maintenance_time,
                "scheduled_maintenance": bot.next_maintenance_time,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch system status: {str(e)}"
        )

# Helper functions

def _calculate_daily_pnl(trades: List[Trade]) -> Dict[str, float]:
    """Calculate daily profit/loss from trade history."""
    daily_pnl = {}
    for trade in trades:
        if trade.exit_time and trade.realized_pnl:
            date = trade.exit_time.date().isoformat()
            daily_pnl[date] = daily_pnl.get(date, 0) + trade.realized_pnl
    return daily_pnl

def _calculate_trade_distribution(trades: List[Trade]) -> Dict[str, int]:
    """Calculate distribution of trade outcomes."""
    distribution = {
        "large_wins": 0,  # >3% profit
        "medium_wins": 0,  # 1-3% profit
        "small_wins": 0,  # 0-1% profit
        "small_losses": 0,  # 0-1% loss
        "medium_losses": 0,  # 1-3% loss
        "large_losses": 0,  # >3% loss
    }
    
    for trade in trades:
        if not trade.roi_percentage:
            continue
            
        roi = trade.roi_percentage
        if roi > 3:
            distribution["large_wins"] += 1
        elif roi > 1:
            distribution["medium_wins"] += 1
        elif roi > 0:
            distribution["small_wins"] += 1
        elif roi > -1:
            distribution["small_losses"] += 1
        elif roi > -3:
            distribution["medium_losses"] += 1
        else:
            distribution["large_losses"] += 1
            
    return distribution

def _calculate_exposure_per_asset(trades: List[Trade]) -> Dict[str, float]:
    """Calculate current exposure per trading asset."""
    exposure = {}
    for trade in trades:
        exposure[trade.symbol] = exposure.get(trade.symbol, 0) + (
            trade.size * trade.entry_price
        )
    return exposure

def _calculate_current_drawdown(trades: List[Trade]) -> float:
    """Calculate current drawdown from recent trade history."""
    if not trades:
        return 0.0
    
    peak = 0
    current = 0
    for trade in trades:
        if trade.realized_pnl:
            current += trade.realized_pnl
            peak = max(peak, current)
    
    return ((peak - current) / peak * 100) if peak > 0 else 0

def _calculate_max_drawdown(trades: List[Trade]) -> float:
    """Calculate maximum drawdown from trade history."""
    if not trades:
        return 0.0
    
    peak = 0
    current = 0
    max_drawdown = 0
    
    for trade in trades:
        if trade.realized_pnl:
            current += trade.realized_pnl
            peak = max(peak, current)
            drawdown = (peak - current) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown

def _calculate_average_drawdown(trades: List[Trade]) -> float:
    """Calculate average drawdown from trade history."""
    if not trades:
        return 0.0
    
    drawdowns = []
    peak = 0
    current = 0
    
    for trade in trades:
        if trade.realized_pnl:
            current += trade.realized_pnl
            peak = max(peak, current)
            if peak > 0:
                drawdown = (peak - current) / peak * 100
                if drawdown > 0:
                    drawdowns.append(drawdown)
    
    return sum(drawdowns) / len(drawdowns) if drawdowns else 0

def _identify_drawdown_periods(trades: List[Trade]) -> List[Dict]:
    """Identify significant drawdown periods from trade history."""
    periods = []
    peak = 0
    current = 0
    start_time = None
    
    for trade in trades:
        if trade.realized_pnl:
            current += trade.realized_pnl
            if current > peak:
                peak = current
                if start_time:  # End of drawdown period
                    periods.append({
                        "start": start_time,
                        "end": trade.exit_time,
                        "drawdown": ((peak - current) / peak * 100) if peak > 0 else 0
                    })
                    start_time = None
            elif peak > 0 and not start_time and (peak - current) / peak > 0.05:  # 5% threshold
                start_time = trade.exit_time
    
    return periods

def _calculate_volatility_metrics(bot: TradingBot) -> Dict:
    """Calculate volatility metrics for active trading pairs."""
    metrics = {}
    for symbol in bot.trading_pairs:
        try:
            volatility = bot.exchange_client.get_market_volatility(symbol)
            metrics[symbol] = {
                "current_volatility": volatility,
                "is_high_volatility": volatility > bot.risk_manager.params.volatility_threshold,
                "volatility_threshold": bot.risk_manager.params.volatility_threshold
            }
        except Exception:
            continue
    return metrics

def _get_system_load() -> Dict:
    """Get system loa
