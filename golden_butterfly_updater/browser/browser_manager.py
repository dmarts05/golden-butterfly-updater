import asyncio
from typing import Self, cast

from loguru import logger
from pyvirtualdisplay.display import Display
from zendriver import Browser, Element, Tab, start

from golden_butterfly_updater.browser.browser_exceptions import (
    ElementNotFoundError,
    NavigationError,
)
from golden_butterfly_updater.browser.delays import Delays


class BrowserManager:
    """
    Manages browser instance and utilities such as navigation, finding elements, and delays.
    Automatically initializes and closes the browser instance.
    """

    _delays: Delays
    """Delays configuration."""
    _display: Display | None
    """Virtual display instance if enabled."""
    _browser: Browser | None
    """Browser instance."""

    def __init__(
        self,
        delays: Delays,
        use_virtual_display: bool,
    ) -> None:
        self._delays = delays
        self._display = (
            Display(visible=False, size=(1920, 1080)) if use_virtual_display else None
        )
        self._browser = None

    async def __aenter__(self) -> Self:
        """
        Starts a virtual display if enabled and initializes the browser instance on entering a context.
        """
        self._start_virtual_display()
        self._browser = await self._start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Stops the browser instance and virtual display if enabled on exiting a context.
        """
        await self._stop_browser()
        self._stop_virtual_display()

    @property
    def browser(self) -> Browser:
        """
        Returns the active browser instance.
        :raises RuntimeError: If the browser is not running.
        """
        if self._browser is None:
            raise RuntimeError(
                "Browser is not running. Ensure the manager is in a context."
            )
        return self._browser

    async def navigate_to(self, url: str) -> Tab:
        """
        Navigates to a URL using the browser.
        :param url: Target URL.
        :return: Browser page.
        :raises NavigationError: If navigation fails.
        """
        try:
            page = await self.browser.get(url)
            await self.sleep_with_delay(self._delays.navigate_delay)
            return page
        except Exception as e:
            logger.exception(f"Navigation error to {url}: {e}")
            raise NavigationError(url) from e

    async def find_element(
        self, parent: Tab | Element, selector: str, error_message: str | None = None
    ) -> Element:
        """
        Finds an element by its selector or raises an exception.
        :param parent: Parent element or page.
        :param selector: CSS selector for the element.
        :param error_message: Error message if the element is not found.
        :return: Found element.
        :raises ElementNotFoundError: If the element is not found.
        """
        try:
            element = (
                await parent.wait_for(selector, timeout=self._delays.wait_timeout)
                if isinstance(parent, Tab)
                else await parent.query_selector(selector)
            )
            if isinstance(element, list):
                element = cast(list[Element], element)[0] if element else None

            if not isinstance(element, Element):
                error_message = error_message or "Element not found"
                logger.error(f"{error_message} (Selector: {selector})")
                raise ElementNotFoundError(selector, error_message)
            return element
        except asyncio.TimeoutError as e:
            error_message = error_message or "Element not found"
            logger.error(f"{error_message} (Selector: {selector})")
            raise ElementNotFoundError(selector, error_message) from e

    async def find_all_elements(
        self, parent: Tab | Element, selector: str, error_message: str | None = None
    ) -> list[Element]:
        """
        Finds all elements by their selector or raises an exception.
        :param parent: Parent element or page.
        :param selector: CSS selector for the elements.
        :param error_message: Error message if the elements are not found.
        :return: Found elements.
        :raises ElementNotFoundError: If the elements are not found.
        """
        elements = await parent.query_selector_all(selector)
        if not elements:
            error_message = error_message or "Elements not found"
            logger.error(f"{error_message} (Selector: {selector})")
            raise ElementNotFoundError(selector, error_message)
        return elements

    async def find_element_by_text(
        self, parent: Tab, text: str, error_message: str | None = None
    ) -> Element:
        """
        Finds an element by its text or raises an exception.
        :param parent: Parent page.
        :param text: Text content of the element.
        :param error_message: Error message if the element is not found.
        :return: Found element.
        :raises ElementNotFoundError: If the element is not found.
        """
        try:
            element = await parent.find_element_by_text(text)
            if not isinstance(element, Element):
                error_message = error_message or "Element not found"
                logger.error(f"{error_message} (Text: {text})")
                raise ElementNotFoundError(text, error_message)
            return element
        except Exception as e:
            error_message = error_message or "Element not found"
            logger.error(f"{error_message} (Text: {text})")
            raise ElementNotFoundError(text, error_message) from e

    async def find_all_elements_by_text(
        self, parent: Tab, text: str, error_message: str | None = None
    ) -> list[Element]:
        """
        Finds all elements by their text or raises an exception.
        :param parent: Parent page.
        :param text: Text content of the elements.
        :param error_message: Error message if the elements are not found.
        :return: Found elements.
        :raises ElementNotFoundError: If the elements are not found.
        """
        elements = await parent.find_elements_by_text(text)
        if not elements:
            error_message = error_message or "Elements not found"
            logger.error(f"{error_message} (Text: {text})")
            raise ElementNotFoundError(text, error_message)
        return elements

    async def click_element(self, element: Element) -> None:
        """
        Clicks on an element.
        :param element: Element to click.
        """
        await element.click()
        await self.sleep_with_delay(self._delays.action_delay)

    async def send_keys_to_element(self, element: Element, keys: str) -> None:
        """
        Sends keys to an element.
        :param element: Element to send keys to.
        :param keys: Keys to send.
        """
        await element.send_keys(keys)
        await self.sleep_with_delay(self._delays.action_delay)

    async def sleep_with_delay(self, delay: float) -> None:
        """
        Waits for a specified delay.
        """
        logger.debug(f"Sleeping for {delay:.2f} seconds.")
        await self.browser.sleep(delay)

    def _start_virtual_display(self) -> None:
        """
        Starts the virtual display if enabled.
        """
        if self._display:
            logger.info("Starting virtual display...")
            self._display.start()
            logger.info("Virtual display started.")

    def _stop_virtual_display(self) -> None:
        """
        Stops the virtual display if enabled.
        """
        if self._display:
            logger.info("Stopping virtual display...")
            self._display.stop()
            logger.info("Virtual display stopped.")

    async def _start_browser(self) -> Browser:
        """
        Starts the browser instance.
        :return: Browser instance.
        """
        logger.info("Starting browser...")
        try:
            browser = await start(headless=False)
            logger.info("Browser started successfully.")
            return browser
        except Exception as e:
            logger.exception(f"Failed to start browser: {e}")
            raise

    async def _stop_browser(self) -> None:
        """
        Stops the browser instance.
        """
        if self._browser is not None:
            logger.info("Stopping browser...")
            try:
                await self._browser.stop()
                logger.info("Browser stopped successfully.")
            except Exception as e:
                logger.exception(f"Failed to stop browser: {e}")
            finally:
                self._browser = None
