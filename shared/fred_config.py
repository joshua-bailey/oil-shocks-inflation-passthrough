"""
FRED API Configuration

This module provides a pre-configured FRED client for use across all notebooks.
The API key is loaded from the .env file in the caller's project directory.

Usage:
    from shared.fred_config import get_fred_client

    fred = get_fred_client()
    data = fred.get_series('GDP')
"""

import os
from dotenv import load_dotenv, find_dotenv
from fredapi import Fred


def get_fred_client() -> Fred:
    """
    Returns a pre-configured FRED client.

    The .env file is located by walking up from the current working directory.
    Each project should have its own .env with FRED_API_KEY.

    Returns:
        Fred: A fredapi.Fred instance ready to fetch data.

    Raises:
        ValueError: If FRED_API_KEY is not found in environment

    Example:
        fred = get_fred_client()
        gdp = fred.get_series('GDP')
        unemployment = fred.get_series('UNRATE')
    """
    load_dotenv(find_dotenv())

    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        raise ValueError(
            "FRED_API_KEY not found. "
            "Please set it in the .env file in your project root. "
            "Get your free API key from: https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    return Fred(api_key=api_key)


def get_series_last_n(series_id: str, n: int = 8) -> 'pd.Series':
    """
    Convenience function to get the last N observations of a series.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE')
        n: Number of most recent observations to return

    Returns:
        pandas Series with the last N observations
    """
    fred = get_fred_client()
    data = fred.get_series(series_id)
    return data.tail(n)
