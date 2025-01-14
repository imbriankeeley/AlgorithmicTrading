from typing import List, Dict, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DataValidationResult:
    """Results of data validation checks."""

    is_valid: bool
    issues: List[str]
    gap_locations: List[datetime]
    anomaly_locations: List[datetime]
    total_missing_values: int


@dataclass
class DataProcessingConfig:
    """Configuration for data processing parameters."""

    resample_interval: str = "1min"  # Default to 1-minute intervals
    fill_gaps: bool = True
    remove_outliers: bool = True
    outlier_std_threshold: float = 3.0
    min_volume_threshold: float = 0.01
    validate_data: bool = True
    max_gap_threshold: timedelta = timedelta(minutes=5)
    normalize_volume: bool = True
    add_indicators: bool = True
    cache_processed_data: bool = True
    cache_dir: str = "data/cache"


class HistoricalDataProcessor:
    """
    Processes and prepares historical cryptocurrency data for backtesting.
    Handles data cleaning, normalization, validation, and feature engineering.
    """

    def __init__(self, config: Optional[DataProcessingConfig] = None):
        """
        Initialize the data processor with configuration.

        Args:
            config: Processing configuration parameters
        """
        self.config = config or DataProcessingConfig()
        self._setup_cache_dir()

    def _setup_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        if self.config.cache_processed_data:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)

    def _validate_raw_data(self, df: pd.DataFrame) -> DataValidationResult:
        """
        Validate raw data for common issues.

        Args:
            df: Raw price data DataFrame

        Returns:
            DataValidationResult with validation details
        """
        issues = []
        gap_locations = []
        anomaly_locations = []
        total_missing = df.isna().sum().sum()

        # Check for required columns
        required_columns = {"open", "high", "low", "close", "volume"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")

        # Check for duplicated timestamps
        duplicates = df.index.duplicated()
        if duplicates.any():
            issues.append(f"Found {duplicates.sum()} duplicate timestamps")

        # Check for gaps in data
        if len(df) > 1:
            time_diff = df.index.to_series().diff()
            expected_diff = pd.Timedelta(self.config.resample_interval)
            gaps = time_diff[time_diff > expected_diff]
            if not gaps.empty:
                gap_locations.extend(gaps.index)
                issues.append(f"Found {len(gaps)} time gaps in data")

        # Check for price anomalies
        if "close" in df.columns:
            price_std = df["close"].std()
            price_mean = df["close"].mean()
            threshold = self.config.outlier_std_threshold * price_std
            outliers = df[abs(df["close"] - price_mean) > threshold]
            if not outliers.empty:
                anomaly_locations.extend(outliers.index)
                issues.append(f"Found {len(outliers)} price anomalies")

        # Check for zero or negative prices
        if "close" in df.columns and (df["close"] <= 0).any():
            issues.append("Found zero or negative prices")

        return DataValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            gap_locations=gap_locations,
            anomaly_locations=anomaly_locations,
            total_missing_values=total_missing,
        )

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean raw data by handling missing values and outliers.

        Args:
            df: Raw price data DataFrame

        Returns:
            Cleaned DataFrame
        """
        # Create a copy to avoid modifying original data
        cleaned = df.copy()

        # Remove rows with all missing values
        cleaned = cleaned.dropna(how="all")

        # Handle outliers if configured
        if self.config.remove_outliers:
            for col in ["open", "high", "low", "close"]:
                if col in cleaned.columns:
                    mean = cleaned[col].mean()
                    std = cleaned[col].std()
                    threshold = self.config.outlier_std_threshold * std
                    cleaned[col] = cleaned[col].clip(
                        lower=mean - threshold, upper=mean + threshold
                    )

        # Forward fill small gaps
        if self.config.fill_gaps:
            cleaned = cleaned.fillna(method="ffill", limit=5)

        # Filter out low volume periods
        if self.config.min_volume_threshold > 0:
            cleaned = cleaned[cleaned["volume"] >= self.config.min_volume_threshold]

        return cleaned

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data for consistency.

        Args:
            df: Cleaned price data DataFrame

        Returns:
            Normalized DataFrame
        """
        normalized = df.copy()

        # Normalize volume if configured
        if self.config.normalize_volume and "volume" in normalized.columns:
            max_volume = normalized["volume"].max()
            if max_volume > 0:  # Prevent division by zero
                normalized["volume"] = normalized["volume"] / max_volume

        # Ensure OHLC prices are properly ordered
        if all(col in normalized.columns for col in ["open", "high", "low", "close"]):
            normalized["high"] = normalized[["open", "high", "close"]].max(axis=1)
            normalized["low"] = normalized[["open", "low", "close"]].min(axis=1)

        return normalized

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataset.

        Args:
            df: Normalized price data DataFrame

        Returns:
            DataFrame with additional technical indicators
        """
        enhanced = df.copy()

        # Basic indicators
        enhanced["returns"] = enhanced["close"].pct_change()
        enhanced["log_returns"] = np.log1p(enhanced["returns"])

        # Volatility (20-period)
        enhanced["volatility"] = enhanced["returns"].rolling(window=20).std()

        # Volume indicators
        if "volume" in enhanced.columns:
            enhanced["volume_ma"] = enhanced["volume"].rolling(window=20).mean()
            enhanced["volume_std"] = enhanced["volume"].rolling(window=20).std()

        # Price momentum
        enhanced["momentum"] = enhanced["close"].pct_change(periods=10)

        # Moving averages
        enhanced["sma_10"] = enhanced["close"].rolling(window=10).mean()
        enhanced["sma_20"] = enhanced["close"].rolling(window=20).mean()
        enhanced["sma_50"] = enhanced["close"].rolling(window=50).mean()

        # Remove initial NaN values created by indicators
        enhanced = enhanced.dropna()

        return enhanced

    def _cache_key(self, symbol: str, start_date: datetime, end_date: datetime) -> str:
        """
        Generate cache key for processed data.

        Args:
            symbol: Trading pair symbol
            start_date: Start of data range
            end_date: End of data range

        Returns:
            Cache key string
        """
        return f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

    def _save_to_cache(self, df: pd.DataFrame, cache_key: str) -> None:
        """
        Save processed data to cache.

        Args:
            df: Processed DataFrame
            cache_key: Cache identifier
        """
        if self.config.cache_processed_data:
            cache_path = Path(self.config.cache_dir) / f"{cache_key}.parquet"
            df.to_parquet(cache_path)

    def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """
        Load processed data from cache.

        Args:
            cache_key: Cache identifier

        Returns:
            Cached DataFrame if available, else None
        """
        if not self.config.cache_processed_data:
            return None

        cache_path = Path(self.config.cache_dir) / f"{cache_key}.parquet"
        if cache_path.exists():
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                return None
        return None

    def process_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[pd.DataFrame, DataValidationResult]:
        """
        Process historical data for backtesting.

        Args:
            df: Raw price data DataFrame
            symbol: Trading pair symbol
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Tuple of (processed_data, validation_result)
        """
        # Generate cache key and check cache
        if start_date and end_date:
            cache_key = self._cache_key(symbol, start_date, end_date)
            cached_data = self._load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data, DataValidationResult(
                    is_valid=True,
                    issues=[],
                    gap_locations=[],
                    anomaly_locations=[],
                    total_missing_values=0,
                )

        # Validate raw data
        validation_result = self._validate_raw_data(df)
        if self.config.validate_data and not validation_result.is_valid:
            logger.warning(f"Data validation issues: {validation_result.issues}")

        # Process data
        processed = df.copy()

        # Apply date filters if provided
        if start_date:
            processed = processed[processed.index >= start_date]
        if end_date:
            processed = processed[processed.index <= end_date]

        # Main processing steps
        processed = self._clean_data(processed)
        processed = self._normalize_data(processed)

        # Add technical indicators if configured
        if self.config.add_indicators:
            processed = self._add_technical_indicators(processed)

        # Cache processed data if configured
        if start_date and end_date:
            self._save_to_cache(processed, cache_key)

        return processed, validation_result

    def prepare_features(
        self, df: pd.DataFrame, feature_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Prepare feature matrix for strategy development or analysis.

        Args:
            df: Processed price data DataFrame
            feature_columns: Optional list of columns to include

        Returns:
            Feature DataFrame
        """
        if feature_columns is None:
            # Default feature set
            feature_columns = [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "returns",
                "volatility",
                "momentum",
            ]

        # Select available features
        available_features = [col for col in feature_columns if col in df.columns]
        features = df[available_features].copy()

        # Handle any remaining missing values
        features = features.fillna(method="ffill").fillna(0)

        return features

    def get_data_info(self, df: pd.DataFrame) -> Dict:
        """
        Get summary information about the processed dataset.

        Args:
            df: Processed DataFrame

        Returns:
            Dictionary with dataset information
        """
        return {
            "start_date": df.index.min(),
            "end_date": df.index.max(),
            "total_records": len(df),
            "columns": list(df.columns),
            "missing_values": df.isna().sum().to_dict(),
            "data_frequency": pd.infer_freq(df.index),
            "memory_usage": df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
        }
