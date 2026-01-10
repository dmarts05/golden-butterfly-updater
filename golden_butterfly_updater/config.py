import re
from dataclasses import dataclass
from typing import Any

import yaml

from golden_butterfly_updater.browser.delays import DelayProfile, Delays

# Regex patterns for validation
PHONE_COUNTRY_CODE_PATTERN = re.compile(r"^\+\d{1,4}$")
PHONE_NUMBER_PATTERN = re.compile(r"^\d{5,15}$")
PIN_PATTERN = re.compile(r"^\d{4}$")


@dataclass(slots=True, frozen=True, kw_only=True)
class BrowserConfig:
    """
    Holds browser configuration.
    """

    headless: bool
    """Whether to run the browser in headless mode."""
    delay_profile: DelayProfile
    """The delay profile to use for browser interactions."""

    @property
    def delays(self) -> Delays:
        """
        Returns the Delays logic object based on the configured profile.

        :return: Delays object.
        """
        return Delays(self.delay_profile)


@dataclass(slots=True, frozen=True, kw_only=True)
class TradeRepublicAccountConfig:
    """
    Holds Trade Republic account configuration.
    """

    phone_country_code: str
    """Phone country code (e.g., +34, +49)."""
    phone_number: str
    """Local phone number (digits only)."""
    pin: str
    """Account 4-digit PIN."""

    def __post_init__(self):
        """
        Validates the phone country code, phone number, and PIN patterns.
        """
        if not PHONE_COUNTRY_CODE_PATTERN.match(self.phone_country_code):
            raise ValueError(
                f"Invalid phone country code '{self.phone_country_code}'. "
                "Must match pattern e.g., +34, +1."
            )

        if not PHONE_NUMBER_PATTERN.match(self.phone_number):
            raise ValueError(
                f"Invalid phone number '{self.phone_number}'. Must be 5-15 digits."
            )

        if not PIN_PATTERN.match(self.pin):
            raise ValueError(f"Invalid PIN '{self.pin}'. Must be exactly 4 digits.")


@dataclass(slots=True, frozen=True, kw_only=True)
class Config:
    """
    Holds application configuration.
    """

    browser_config: BrowserConfig
    """Browser configuration."""
    trade_republic_config: TradeRepublicAccountConfig
    """Trade Republic account configuration."""


def _load_yaml(file_path: str) -> dict[str, Any]:
    """
    Loads a YAML file and returns its content as a dictionary.

    :param file_path: Path to the YAML file.
    :return: Dictionary with the YAML content.
    """
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ValueError(f"Configuration file '{file_path}' not found")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


def _get_browser_config(browser_data: dict[str, Any] | None) -> BrowserConfig:
    """
    Parses and validates the browser configuration section.

    :param browser_data: Raw dictionary containing browser options.
    :return: Validated BrowserConfig object.
    """
    if not browser_data:
        raise ValueError("Missing 'browser_options' section in configuration.")

    try:
        delay_profile_val = browser_data["delay_profile"]
        profile = DelayProfile(delay_profile_val)
        return BrowserConfig(
            headless=browser_data["headless"],
            delay_profile=profile,
        )
    except KeyError as e:
        raise ValueError(f"Missing required field in 'browser_options': {e}")
    except ValueError as e:
        raise ValueError(f"Invalid value in 'browser_options': {e}")


def _get_trade_republic_config(
    tr_data: dict[str, Any] | None,
) -> TradeRepublicAccountConfig:
    """
    Parses and validates the Trade Republic configuration section.

    :param tr_data: Raw dictionary containing Trade Republic options.
    :return: Validated TradeRepublicAccountConfig object.
    """
    if not tr_data:
        raise ValueError("Missing 'trade_republic' section in configuration.")

    try:
        return TradeRepublicAccountConfig(
            phone_country_code=str(tr_data["phone_country_code"]),
            phone_number=str(tr_data["phone_number"]),
            pin=str(tr_data["pin"]),
        )
    except KeyError as e:
        raise ValueError(f"Missing required field in 'trade_republic': {e}")
    except ValueError as e:
        raise ValueError(f"Validation failed for 'trade_republic': {e}")


def load_config_from_yaml(file_path: str = "config.yml") -> Config:
    """
    Loads application configuration from a YAML file.
    Manually maps YAML keys to dataclasses and validates types.
    """
    raw_config = _load_yaml(file_path)

    browser_config = _get_browser_config(raw_config.get("browser_options"))
    trade_republic_config = _get_trade_republic_config(raw_config.get("trade_republic"))

    return Config(
        browser_config=browser_config,
        trade_republic_config=trade_republic_config,
    )
