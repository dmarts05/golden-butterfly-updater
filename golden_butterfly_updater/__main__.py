import asyncio

from loguru import logger

from golden_butterfly_updater.browser.browser_manager import BrowserManager
from golden_butterfly_updater.config import load_config_from_yaml
from golden_butterfly_updater.portfolio_updater.google_portfolio_updater import (
    GooglePortfolioUpdater,
)
from golden_butterfly_updater.scraper.asset import Asset
from golden_butterfly_updater.scraper.bank_scraper import BankScraper
from golden_butterfly_updater.scraper.my_investor_bank_scraper import (
    MyInvestorBankScraper,
)
from golden_butterfly_updater.scraper.trade_republic_bank_scraper import (
    TradeRepublicBankScraper,
)


async def run() -> None:
    logger.info("Starting Golden Butterfly Updater...")

    logger.info("Loading configuration...")
    try:
        config = load_config_from_yaml()
    except ValueError as e:
        logger.exception(f"Error while loading configuration: {e}")
        return
    logger.debug(config)
    logger.info("Configuration loaded")

    assets: list[Asset] = []
    async with BrowserManager(
        delays=config.browser_config.delays,
        use_virtual_display=config.browser_config.headless,
    ) as browser_manager:
        scrapers: list[BankScraper] = []
        if config.trade_republic_config is not None:
            scrapers.append(
                TradeRepublicBankScraper(
                    browser_manager=browser_manager,
                    account=config.trade_republic_config,
                )
            )
        if config.my_investor_config is not None:
            scrapers.append(
                MyInvestorBankScraper(
                    browser_manager=browser_manager, account=config.my_investor_config
                )
            )

        for scraper in scrapers:
            scraper_name = scraper.__class__.__name__
            logger.info(f"Running scraper: {scraper_name}")
            try:
                scraper_assets = await scraper.get_assets()
                assets.extend(scraper_assets)
            except Exception as e:
                logger.exception(f"Error while running scraper {scraper_name}: {e}")

    logger.info(f"Total assets retrieved: {len(assets)}")
    logger.debug(assets)

    logger.info("Updating spreadsheet...")

    sheets_updater = GooglePortfolioUpdater(
        credentials_path=config.google_sheets_config.credentials_path,
        sheet_name=config.google_sheets_config.sheet_name,
    )
    try:
        sheets_updater.update_portfolio(assets)
    except Exception as e:
        logger.exception(f"Error while updating spreadsheet: {e}")
        return

    logger.info("Spreadsheet update completed.")

    logger.info("Golden Butterfly Updater finished.")


def main() -> None:
    logger.add(
        "golden_butterfly_updater.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
