from abc import ABC, abstractmethod

from golden_butterfly_updater.scraper.asset import Asset


class PortfolioUpdater(ABC):
    """
    Abstract base class for portfolio updaters.
    """

    @abstractmethod
    def update_portfolio(self, assets: list[Asset]) -> None:
        """
        Updates the portfolio with the given list of assets.
        :param assets: List of Asset objects to update the portfolio with.
        """
        pass
