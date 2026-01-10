from abc import ABC, abstractmethod

from golden_butterfly_updater.browser.browser_manager import BrowserManager
from golden_butterfly_updater.scraper.asset import Asset


class BankScraper(ABC):
    """Abstract base class for bank account scrapers."""

    _browser_manager: BrowserManager
    """Browser manager for handling browser interactions."""

    def __init__(self, browser_manager: BrowserManager) -> None:
        self._browser_manager = browser_manager

    @abstractmethod
    async def get_assets(self) -> list[Asset]:
        """
        Retrieve a list of assets from the bank account.

        :return: List of assets.
        """
        ...
