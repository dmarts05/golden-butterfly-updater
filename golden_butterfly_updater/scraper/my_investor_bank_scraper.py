from loguru import logger

from golden_butterfly_updater.browser.browser_exceptions import (
    ElementNotFoundError,
    NavigationError,
)
from golden_butterfly_updater.browser.browser_manager import BrowserManager
from golden_butterfly_updater.config import MyInvestorAccountConfig
from golden_butterfly_updater.scraper.asset import Asset, AssetType
from golden_butterfly_updater.scraper.bank_scraper import BankScraper
from golden_butterfly_updater.scraper.scraper_exceptions import LoginError


class MyInvestorBankScraper(BankScraper):
    """
    Scraper for MyInvestor Bank.
    """

    _account: MyInvestorAccountConfig
    """MyInvestor account configuration."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        account: MyInvestorAccountConfig,
    ) -> None:
        super().__init__(browser_manager)
        self._account = account

    async def get_assets(self) -> list[Asset]:
        try:
            logger.info(f"Logging into MyInvestor as {self._account.username}...")
            await self._log_in()
            logger.info("Logged in successfully")

            logger.info("Retrieving cash balance...")
            cash_asset = await self._retrieve_cash_balance()
            logger.info("Cash balance retrieved.")

            logger.info("Retrieving investment assets based on configuration...")
            investment_assets = await self._retrieve_configured_assets()
            logger.info("Investment assets retrieved.")

            assets = [cash_asset] + investment_assets
            return assets

        except LoginError as e:
            logger.error(f"Login failed: {e}")
        except NavigationError as e:
            logger.error(f"Navigation failed: {e}")
        except ElementNotFoundError as e:
            logger.error(f"Element error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")

        return []

    async def _log_in(self) -> None:
        """
        Logs into MyInvestor.
        """
        page = await self._browser_manager.navigate_to(
            "https://newapp.myinvestor.es/auth/signin/?data_traffic_origin=Web_Home"
        )

        await self._enter_username(page)
        await self._enter_password(page)
        await self._click_login_button(page)
        await self._ensure_logged_in(page)

    async def _enter_username(self, page) -> None:
        """
        Enters the username (DNI/NIE).
        :param page: Current browser page.
        """
        username_input = await self._browser_manager.find_element(
            page,
            "input[placeholder='DNI / NIE / Pasaporte']",
            "Username input not found",
        )
        await self._browser_manager.send_keys_to_element(
            username_input, self._account.username
        )

    async def _enter_password(self, page) -> None:
        """
        Enters the password.
        :param page: Current browser page.
        """
        password_input = await self._browser_manager.find_element(
            page,
            "input[type='password']",
            "Password input not found",
        )
        await self._browser_manager.send_keys_to_element(
            password_input, self._account.password.get_secret_value()
        )

    async def _click_login_button(self, page) -> None:
        """
        Clicks the login submission button.
        :param page: Current browser page.
        """
        login_button = await self._browser_manager.find_element(
            page,
            "button[type='submit']",
            "Login submit button not found",
        )
        await self._browser_manager.click_element(login_button)

    async def _ensure_logged_in(self, page) -> None:
        """
        Ensures that the user is logged in by checking for the dashboard element.
        :param page: Current browser page.
        :raises LoginError: If the user is not logged in.
        """
        try:
            await self._browser_manager.find_element(
                page,
                "a[href='/app/products'][aria-current='page']",
                "Dashboard link not found; login may have failed.",
            )
        except ElementNotFoundError:
            raise LoginError("Login verification failed; user may not be logged in.")

    async def _retrieve_cash_balance(self) -> Asset:
        """
        Retrieves the cash balance from MyInvestor.
        :return: Cash balance as an Asset.
        """
        page = await self._browser_manager.navigate_to(
            "https://newapp.myinvestor.es/app/products"
        )
        cash_account_anchor = await self._browser_manager.find_element(
            page,
            "a[href^='/app/products/cash-accounts/']",
            "Cash account link not found",
        )
        await self._browser_manager.click_element(cash_account_anchor)

        balance_element = await self._browser_manager.find_element(
            page,
            "div > span + h2 > span[data-private='true']",
            "Cash balance element not found",
        )
        balance_value = float(
            balance_element.text.replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        return Asset(
            name="MyInvestor Cash", amount=balance_value, asset_type=AssetType.CASH
        )

    async def _retrieve_configured_assets(self) -> list[Asset]:
        """
        Orchestrates the retrieval of assets based on the configuration.
        Separates assets into Index Funds and ETFs to optimize navigation.
        :return: List of retrieved Asset objects.
        """
        found_assets: list[Asset] = []

        # Split assets by product type
        # index_funds = [
        #     a for a in self._account.assets if a.product_type == ProductType.INDEX_FUND
        # ]
        # etfs = [a for a in self._account.assets if a.product_type == ProductType.ETF]

        # TODO

        return found_assets
