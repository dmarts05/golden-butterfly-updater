from dataclasses import dataclass
from enum import Enum


class ProductType(Enum):
    """
    Enumeration of financial product types.
    """

    ETF = "etf"
    INDEX_FUND = "index_fund"


class AssetType(Enum):
    """
    Enumeration of financial asset types matching the portfolio structure.
    """

    CASH = "cash"
    LONG_TERM_TREASURY = "long_term_treasury"
    GOLD = "gold"
    SMALL_CAP_STOCKS = "small_cap_stocks"
    LARGE_CAP_STOCKS = "large_cap_stocks"


@dataclass(frozen=True, slots=True, kw_only=True)
class Asset:
    """Representation of a financial asset."""

    name: str
    """Name of the asset."""
    amount: float
    """Amount of the asset."""
    asset_type: AssetType
    """Type of the asset."""
