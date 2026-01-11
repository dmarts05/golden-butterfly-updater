from loguru import logger
from zendriver import Element

from golden_butterfly_updater.browser.browser_exceptions import (
    ElementNotFoundError,
    NavigationError,
)
from golden_butterfly_updater.browser.browser_manager import BrowserManager
from golden_butterfly_updater.config import MyInvestorAccountConfig, TrackedAssetConfig
from golden_butterfly_updater.scraper.asset import Asset, AssetType, ProductType
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
        await self._navigate_to_cash_account(page)
        balance_value = await self._get_cash_balance_value(page)
        return Asset(
            name="MyInvestor Cash", amount=balance_value, asset_type=AssetType.CASH
        )

    async def _navigate_to_cash_account(self, page) -> None:
        """
        Navigates to the cash account page.
        :param page: Current browser page.
        """
        cash_account_anchor = await self._browser_manager.find_element(
            page,
            "a[href^='/app/products/cash-accounts/']",
            "Cash account link not found",
        )
        await self._browser_manager.click_element(cash_account_anchor)

    async def _get_cash_balance_value(self, page) -> float:
        """
        Retrieves the cash balance value from the cash account page.
        :param page: Current browser page.
        :return: Cash balance as a float.
        """
        balance_element = await self._browser_manager.find_element(
            page,
            "div > span + h2 > span[data-private='true']",
            "Cash balance element not found",
        )
        return self._parse_currency(balance_element.text)

    async def _retrieve_configured_assets(self) -> list[Asset]:
        """
        Orchestrates the retrieval of assets based on the configuration.
        Separates assets into Index Funds and ETFs to optimize navigation.
        :return: List of retrieved Asset objects.
        """
        assets: list[Asset] = []

        index_funds = [
            a for a in self._account.assets if a.product_type == ProductType.INDEX_FUND
        ]
        etfs = [a for a in self._account.assets if a.product_type == ProductType.ETF]

        if index_funds:
            index_assets = await self._retrieve_index_fund_assets(index_funds)
            assets.extend(index_assets)

        if etfs:
            # Placeholder for future ETF implementation
            logger.warning("ETF retrieval is not yet implemented.")

        return assets

    async def _retrieve_index_fund_assets(
        self, index_funds: list[TrackedAssetConfig]
    ) -> list[Asset]:
        """
        Retrieves Index Fund assets based on the provided configuration.
        :param index_funds: List of TrackedAssetConfig for Index Funds.
        :return: List of retrieved Asset objects.
        """
        page = await self._browser_manager.navigate_to(
            "https://newapp.myinvestor.es/app/products"
        )
        await self._navigate_to_index_funds_section(page)

        fund_elements = await self._get_index_fund_elements(page)
        found_assets: list[Asset] = []
        for element in fund_elements:
            href = element.get("href")
            if not href:
                continue

            isin = href.split("/")[-1]
            config = next((c for c in index_funds if c.isin == isin), None)
            if not config:
                continue

            try:
                amount_element = await element.query_selector(
                    "h5 span[data-private='true']"
                )

                if not amount_element:
                    logger.warning(f"Could not find amount for tracked ISIN {isin}")
                    continue

                amount_text = amount_element.text
                amount = self._parse_currency(amount_text)

                name_element = await element.query_selector("div > span > div > span")
                name = (
                    name_element.text.strip() if name_element else f"Index Fund {isin}"
                )

                asset = Asset(name=name, amount=amount, asset_type=config.asset_type)
                found_assets.append(asset)
                logger.debug(f"Found asset: {asset.name} ({isin}) = {asset.amount}")

            except Exception as e:
                logger.error(f"Error extracting data for ISIN {isin}: {e}")

        return found_assets

    async def _navigate_to_index_funds_section(self, page) -> None:
        """
        Navigates to the Index Funds section of the MyInvestor platform.
        :param page: Current browser page.
        """
        index_funds_anchor = await self._browser_manager.find_element(
            page,
            "a[href^='/app/products/investments/funds/']",
            "Index Funds section link not found",
        )
        await self._browser_manager.click_element(index_funds_anchor)

    async def _get_index_fund_elements(self, page) -> list[Element]:
        """
        Retrieves all index fund elements from the investments page.
        :param page: Current browser page.
        :return: List of index fund elements.
        """
        index_fund_elements = await self._browser_manager.find_all_elements(
            page,
            'a[href*="/products/investments/funds/"]:not([href*="security-account"])',
            "No index fund elements found",
        )
        return index_fund_elements

    @staticmethod
    def _parse_currency(text: str) -> float:
        """
        Parses a European currency string (e.g., "2.293,16 €") into a float.
        :param text: Currency string to parse.
        :return: Parsed float value.
        """
        return float(
            text.replace("€", "")
            .replace(".", "")  # Remove thousands separator
            .replace(",", ".")  # Convert decimal separator
            .strip()
        )
