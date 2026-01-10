class ScraperError(Exception):
    """Base exception for scraper errors."""

    pass


class LoginError(ScraperError):
    """Exception raised for login failures."""

    pass
