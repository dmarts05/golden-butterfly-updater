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
    """Trade Republic account configuration."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        account: TradeRepublicAccountConfig,
    ) -> None:
        super().__init__(browser_manager)
        self._account = account

    async def get_assets(self) -> list[Asset]:
        try:
            logger.info(
                f"Logging into Trade Republic as {self._account.phone_number}..."
            )
            await self._log_in()
            logger.info("Logged in successfully")

            logger.info("Retrieving cash balance...")
            cash_asset = await self._retrieve_cash_balance()
            logger.info("Cash balance retrieved.")

            return [cash_asset]

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

        await self._accept_cookies(page)
        await self._set_phone_country_code(page)
        await self._enter_phone_number(page)
        await self._press_next_button(page)
        await self._enter_pin(page)
        await self._enter_confirmation_code(page)
        await self._ensure_logged_in(page)

    async def _accept_cookies(self, page) -> None:
        """
        Accepts cookies on the login page.
        :param page: Current browser page.
        """
        accept_button = await self._browser_manager.find_element(
            page,
            "button.consentCard__action",
            "Cookie accept button not found",
        )
        await self._browser_manager.click_element(accept_button)

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
            f'[id="areaCode-{self._account.phone_country_code}"]',
            f"Country option for {self._account.phone_country_code} not found",
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

    async def _enter_pin(self, page) -> None:
        """
        Enters the PIN in the login form.
        Since the PIN is a 4-digit code, we need to enter each digit separately in its own input field.
        :param page: Current browser page.
        """
        for digit in self._account.pin.get_secret_value():
            pin_input = await self._browser_manager.find_element(
                page,
                ".codeInput__character:not(.-withValue)",
                "Next PIN input not found",
            )
            await self._browser_manager.send_keys_to_element(pin_input, digit)

    async def _enter_confirmation_code(self, page) -> None:
        """
        Enters the confirmation code.
        :param page: Current browser page.
        """
        code = input("Enter the confirmation code: ")

        for digit in code:
            code_input = await self._browser_manager.find_element(
                page,
                ".codeInput__character:not(.-withValue)",
                "Next confirmation code input not found",
            )
            await self._browser_manager.send_keys_to_element(code_input, digit)

    async def _ensure_logged_in(self, page) -> None:
        """
        Ensures that the user is logged in by checking for a known post-login element.
        :param page: Current browser page.
        :raises LoginError: If the user is not logged in.
        """
        try:
            await self._browser_manager.find_element(
                page,
                " #instrumentSearch__q",
                "Login verification element not found",
            )
        except ElementNotFoundError:
            raise LoginError("Login verification failed; user may not be logged in.")

    async def _retrieve_cash_balance(self) -> Asset:
        """
        Retrieves the cash balance from the account overview.
        :return: Cash balance as an Asset.
        """
        page = await self._browser_manager.navigate_to(
            "https://app.traderepublic.com/profile/transactions"
        )

        balance_element = await self._browser_manager.find_element(
            page,
            ".cashBalance__amount",
            "Cash balance element not found",
        )
        balance_value = float(
            balance_element.text.replace("€", "").replace(",", "").strip()
        )
        logger.debug(f"Found cash balance: {balance_value}")
        return Asset(
            name="Trade Republic Cash", amount=balance_value, asset_type=AssetType.CASH
        )
