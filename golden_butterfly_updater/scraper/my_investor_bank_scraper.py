from golden_butterfly_updater.scraper.asset import Asset
from golden_butterfly_updater.scraper.bank_scraper import BankScraper


class MyInvestorBankScraper(BankScraper):
    """Scraper for MyInvestor Bank."""

    async def get_assets(self) -> list[Asset]:
        return []
