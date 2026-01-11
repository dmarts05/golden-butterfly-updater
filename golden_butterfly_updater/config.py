from dataclasses import dataclass
from typing import Any

import yaml

from golden_butterfly_updater.browser.delays import DelayProfile, Delays
from golden_butterfly_updater.regex import (
    ISIN_PATTERN,
    PHONE_COUNTRY_CODE_PATTERN,
    PHONE_NUMBER_PATTERN,
    PIN_PATTERN,
)
from golden_butterfly_updater.scraper.asset import AssetType, ProductType
from golden_butterfly_updater.types import SecretStr


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
    pin: SecretStr
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

        # Validate the raw secret value
        if not PIN_PATTERN.match(self.pin.get_secret_value()):
            raise ValueError("Invalid PIN. Must be exactly 4 digits.")


@dataclass(slots=True, frozen=True, kw_only=True)
class TrackedAssetConfig:
    """
    Configuration for a specific asset to track.
    """

    isin: str
    """The ISIN identifier of the asset."""
    product_type: ProductType
    """The type of product (ETF or Index Fund)."""
    asset_type: AssetType
    """The category of the asset (Gold, Treasury, etc.)."""

    def __post_init__(self):
        """
        Validates the ISIN format.
        """

        if not ISIN_PATTERN.match(self.isin):
            raise ValueError(
                f"Invalid ISIN '{self.isin}'. Must match standard ISIN format."
            )


@dataclass(slots=True, frozen=True, kw_only=True)
class MyInvestorAccountConfig:
    """
    Holds MyInvestor account configuration.
    """

    username: str
    """Username."""
    password: SecretStr
    """Account password."""
    assets: list[TrackedAssetConfig]
    """List of assets to track and scrape."""

    def __post_init__(self):
        """
        Validates that username and password are provided.
        """
        if not self.username:
            raise ValueError("MyInvestor username cannot be empty.")
        if not self.password.get_secret_value():
            raise ValueError("MyInvestor password cannot be empty.")


@dataclass(slots=True, frozen=True, kw_only=True)
class Config:
    """
    Holds application configuration.
    """

    browser_config: BrowserConfig
    """Browser configuration."""
    trade_republic_config: TradeRepublicAccountConfig | None
    """Trade Republic account configuration."""
    my_investor_config: MyInvestorAccountConfig | None
    """MyInvestor account configuration."""


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
) -> TradeRepublicAccountConfig | None:
    """
    Parses and validates the Trade Republic configuration section.

    :param tr_data: Raw dictionary containing Trade Republic options.
    :return: Validated TradeRepublicAccountConfig object or None if missing.
    """
    if not tr_data:
        return None

    try:
        return TradeRepublicAccountConfig(
            phone_country_code=str(tr_data["phone_country_code"]),
            phone_number=str(tr_data["phone_number"]),
            pin=SecretStr(str(tr_data["pin"])),
        )
    except KeyError as e:
        raise ValueError(f"Missing required field in 'trade_republic': {e}")
    except ValueError as e:
        raise ValueError(f"Validation failed for 'trade_republic': {e}")


def _parse_assets_config(assets_data: list[dict[str, Any]]) -> list[TrackedAssetConfig]:
    """
    Parses the list of assets from the configuration.

    :param assets_data: List of dictionaries containing asset details.
    :return: List of TrackedAssetConfig objects.
    """
    parsed_assets = []
    for asset in assets_data:
        try:
            parsed_assets.append(
                TrackedAssetConfig(
                    isin=str(asset["isin"]),
                    product_type=ProductType(asset["product_type"]),
                    asset_type=AssetType(asset["asset_type"]),
                )
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid asset configuration: {asset}. Error: {e}")
    return parsed_assets


def _get_my_investor_config(
    mi_data: dict[str, Any] | None,
) -> MyInvestorAccountConfig | None:
    """
    Parses and validates the MyInvestor configuration section.

    :param mi_data: Raw dictionary containing MyInvestor options.
    :return: Validated MyInvestorAccountConfig object or None if missing.
    """
    if not mi_data:
        return None

    try:
        assets_data = mi_data.get("assets", [])
        return MyInvestorAccountConfig(
            username=str(mi_data["username"]),
            password=SecretStr(str(mi_data["password"])),
            assets=_parse_assets_config(assets_data),
        )
    except KeyError as e:
        raise ValueError(f"Missing required field in 'my_investor': {e}")
    except ValueError as e:
        raise ValueError(f"Validation failed for 'my_investor': {e}")


def load_config_from_yaml(file_path: str = "config.yml") -> Config:
    """
    Loads application configuration from a YAML file.
    Manually maps YAML keys to dataclasses and validates types.

    :param file_path: Path to the YAML configuration file.
    :return: Config object with the loaded configuration.
    """
    raw_config = _load_yaml(file_path)

    browser_config = _get_browser_config(raw_config.get("browser_options"))
    trade_republic_config = _get_trade_republic_config(raw_config.get("trade_republic"))
    my_investor_config = _get_my_investor_config(raw_config.get("my_investor"))

    return Config(
        browser_config=browser_config,
        trade_republic_config=trade_republic_config,
        my_investor_config=my_investor_config,
    )
