class BrowserManagerException(Exception):
    """Base exception for BrowserManager errors."""

    pass


class NavigationError(BrowserManagerException):
    """Raised when navigation to a URL fails."""

    def __init__(self, url: str, message: str = "Failed to navigate to the URL"):
        super().__init__(f"{message}: {url}")


class ElementNotFoundError(BrowserManagerException):
    """Raised when an element is not found."""

    def __init__(self, selector: str, message: str = "Element not found"):
        super().__init__(f"{message} (Selector: {selector})")
