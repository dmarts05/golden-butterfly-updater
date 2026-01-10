from loguru import logger

from golden_butterfly_updater.browser.browser_exceptions import (
    ElementNotFoundError,
    NavigationError,
)
from golden_butterfly_updater.browser.browser_manager import BrowserManager
from golden_butterfly_updater.config import TradeRepublicAccountConfig
from golden_butterfly_updater.scraper.asset import Asset, AssetType
from golden_butterfly_updater.scraper.bank_scraper import BankScraper
from golden_butterfly_updater.scraper.scraper_exceptions import LoginError


class TradeRepublicBankScraper(BankScraper):
    """
    Scraper for Trade Republic Bank.
    """

    _account: TradeRepublicAccountConfig

    def __init__(
        self,
        browser_manager: BrowserManager,
        account: TradeRepublicAccountConfig,
    ) -> None:
        """
        Creates a new Trade Republic scraper.
        :param browser_manager: Browser manager instance.
        :param account: Trade Republic account credentials.
        """
        super().__init__(browser_manager)
        self._account = account

    async def get_assets(self) -> list[Asset]:
        """
        Retrieve a list of assets from the bank account.
        :return: List of assets.
        """
        try:
            logger.info(
                f"Logging into Trade Republic as {self._account.phone_number}..."
            )
            await self._log_in()
            logger.info("Logged in successfully")

            logger.info("Retrieving cash balance...")
            cash_amount = 0.0  # TODO
            logger.info(f"Cash balance retrieved: {cash_amount}€")

            return [
                Asset(
                    name="Trade Republic Cash",
                    amount=cash_amount,
                    asset_type=AssetType.CASH,
                )
            ]

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
        Logs into Trade Republic.
        """
        page = await self._browser_manager.navigate_to(
            "https://app.traderepublic.com/login"
        )

        await self._set_phone_country_code(page)
        await self._enter_phone_number(page)
        await self._press_next_button(page)

    async def _set_phone_country_code(self, page) -> None:
        """
        Sets the phone country code in the login form.
        :param page: Current browser page.
        """
        country_code_input = await self._browser_manager.find_element(
            page,
            ".dropdownList__openButton",
            "Country code input not found",
        )
        await self._browser_manager.click_element(country_code_input)

        country_option = await self._browser_manager.find_element(
            page,
            f"#areaCode-{self._account.phone_country_code}",
            "Country option for Germany not found",
        )
        await self._browser_manager.click_element(country_option)

    async def _enter_phone_number(self, page) -> None:
        """
        Enters the phone number in the login form.
        :param page: Current browser page.
        """
        phone_input = await self._browser_manager.find_element(
            page,
            "#loginPhoneNumber__input",
            "Phone number input not found",
        )
        await self._browser_manager.send_keys_to_element(
            phone_input, self._account.phone_number
        )

    async def _press_next_button(self, page) -> None:
        """
        Presses the "Next" button in the login form.
        :param page: Current browser page.
        """
        next_button = await self._browser_manager.find_element(
            page,
            "button[type='submit']",
            "Next button not found",
        )
        await self._browser_manager.click_element(next_button)

    async def _enter_password(self, page) -> None:
        """
        Enters the password in the login form.
        Since password is a 4 code pin, we need to enter each digit separately in its own input field.
        :param page: Current browser page.
        """
        pin_inputs = await self._browser_manager.find_all_elements(
            page, ".codeInput__character", "PIN inputs not found"
        )

        for pin_input, digit in zip(pin_inputs, self._account.pin):
            await self._browser_manager.send_keys_to_element(pin_input, digit)
