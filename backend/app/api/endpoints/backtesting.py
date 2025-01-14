from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO

from ....core.backtesting.engine import BacktestingEngine, BacktestParameters
from ....core.backtesting.data_processor import (
    HistoricalDataProcessor,
    DataProcessingConfig,
)
from ....core.trading.strategy import MomentumStrategy, StrategyParameters
from ....core.trading.risk_manager import RiskManager, RiskParameters
from ....models.backtest import Backtest
from ....schemas.backtest import (
    BacktestCreate,
    BacktestResponse,
    BacktestResult,
    OptimizationRequest,
    OptimizationResponse,
)
from ....services.database import get_db
from ....dependencies import get_current_user

router = APIRouter()


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    backtest_params: BacktestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Run a backtest with specified parameters.

    Args:
        backtest_params: Parameters for the backtest
        db: Database session
        current_user: Authenticated user info
    """
    try:
        # Initialize strategy with provided parameters
        strategy_params = StrategyParameters(
            short_ema_period=backtest_params.strategy_params.short_ema_period,
            long_ema_period=backtest_params.strategy_params.long_ema_period,
            take_profit_pct=backtest_params.strategy_params.take_profit_pct,
            stop_loss_pct=backtest_params.strategy_params.stop_loss_pct,
            position_size_pct=backtest_params.strategy_params.position_size_pct,
        )

        strategy = MomentumStrategy(parameters=strategy_params)

        # Initialize risk manager
        risk_params = RiskParameters(
            max_position_size=backtest_params.risk_params.max_position_size,
            max_daily_drawdown=backtest_params.risk_params.max_daily_drawdown,
            max_trades_per_day=backtest_params.risk_params.max_trades_per_day,
        )

        risk_manager = RiskManager(parameters=risk_params)

        # Setup backtesting engine
        backtest_config = BacktestParameters(
            initial_capital=backtest_params.initial_capital,
            trading_fees=backtest_params.trading_fees,
            slippage=backtest_params.slippage,
            include_fees=backtest_params.include_fees,
            include_slippage=backtest_params.include_slippage,
        )

        engine = BacktestingEngine(
            strategy=strategy, risk_manager=risk_manager, parameters=backtest_config
        )

        # Process historical data
        data_processor = HistoricalDataProcessor(
            config=DataProcessingConfig(
                resample_interval=backtest_params.data_interval, validate_data=True
            )
        )

        # Load and process data
        processed_data, validation_result = data_processor.process_data(
            df=pd.read_csv(StringIO(backtest_params.historical_data)),
            symbol=backtest_params.symbol,
            start_date=backtest_params.start_date,
            end_date=backtest_params.end_date,
        )

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Data validation failed: {validation_result.issues}",
            )

        # Run backtest
        results = engine.run_backtest(processed_data)

        # Store backtest results in database
        backtest_record = Backtest(
            user_id=current_user["id"],
            symbol=backtest_params.symbol,
            start_date=backtest_params.start_date,
            end_date=backtest_params.end_date,
            strategy_name="MomentumStrategy",
            strategy_params=strategy_params.__dict__,
            risk_params=risk_params.__dict__,
            initial_capital=backtest_params.initial_capital,
            total_return=results.performance_metrics["total_return"],
            sharpe_ratio=results.performance_metrics["sharpe_ratio"],
            max_drawdown=results.drawdown_metrics["max_drawdown"],
            total_trades=results.trade_metrics["total_trades"],
            win_rate=results.trade_metrics["win_rate"],
            profit_factor=results.trade_metrics["profit_factor"],
            execution_time=datetime.utcnow(),
        )

        db.add(backtest_record)
        db.commit()
        db.refresh(backtest_record)

        return BacktestResponse(
            id=backtest_record.id,
            results=BacktestResult(
                performance_metrics=results.performance_metrics,
                trade_metrics=results.trade_metrics,
                drawdown_metrics=results.drawdown_metrics,
                equity_curve=results.equity_curve.to_dict(),
                trades=[trade.to_dict() for trade in results.trades],
            ),
            parameters=backtest_params,
            execution_time=backtest_record.execution_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run backtest: {str(e)}")


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_strategy(
    optimization_request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Optimize strategy parameters using historical data.

    Args:
        optimization_request: Parameters for optimization
        db: Database session
        current_user: Authenticated user info
    """
    try:
        # Initialize base strategy and engine
        strategy = MomentumStrategy()
        engine = BacktestingEngine(strategy=strategy)

        # Process historical data
        data_processor = HistoricalDataProcessor()
        processed_data, validation_result = data_processor.process_data(
            df=pd.read_csv(StringIO(optimization_request.historical_data)),
            symbol=optimization_request.symbol,
            start_date=optimization_request.start_date,
            end_date=optimization_request.end_date,
        )

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Data validation failed: {validation_result.issues}",
            )

        # Run optimization
        best_params, best_results = engine.optimize_strategy(
            data=processed_data,
            parameter_ranges=optimization_request.parameter_ranges,
            optimization_metric=optimization_request.optimization_metric,
        )

        return OptimizationResponse(
            best_parameters=best_params,
            performance_metrics=best_results.performance_metrics,
            trade_metrics=best_results.trade_metrics,
            drawdown_metrics=best_results.drawdown_metrics,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize strategy: {str(e)}"
        )


@router.get("/history", response_model=List[BacktestResponse])
async def get_backtest_history(
    skip: int = 0,
    limit: int = 10,
    symbol: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get historical backtest results for the user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        symbol: Optional symbol filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        db: Database session
        current_user: Authenticated user info
    """
    query = db.query(Backtest).filter(Backtest.user_id == current_user["id"])

    if symbol:
        query = query.filter(Backtest.symbol == symbol)
    if start_date:
        query = query.filter(Backtest.start_date >= start_date)
    if end_date:
        query = query.filter(Backtest.end_date <= end_date)

    total = query.count()
    backtests = (
        query.order_by(Backtest.execution_time.desc()).offset(skip).limit(limit).all()
    )

    return [BacktestResponse.from_orm(backtest) for backtest in backtests]


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_results(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed results for a specific backtest.

    Args:
        backtest_id: ID of the backtest to retrieve
        db: Database session
        current_user: Authenticated user info
    """
    backtest = (
        db.query(Backtest)
        .filter(Backtest.id == backtest_id, Backtest.user_id == current_user["id"])
        .first()
    )

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return BacktestResponse.from_orm(backtest)


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a specific backtest record.

    Args:
        backtest_id: ID of the backtest to delete
        db: Database session
        current_user: Authenticated user info
    """
    backtest = (
        db.query(Backtest)
        .filter(Backtest.id == backtest_id, Backtest.user_id == current_user["id"])
        .first()
    )

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    db.delete(backtest)
    db.commit()

    return {"message": f"Backtest {backtest_id} deleted successfully"}
