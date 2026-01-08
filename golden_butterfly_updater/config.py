from dataclasses import dataclass
from typing import Any

import yaml

from golden_butterfly_updater.browser.delays import DelayProfile, Delays


@dataclass(slots=True, frozen=True, kw_only=True)
class BrowserConfig:
    """
    Holds browser configuration.
    """

    headless: bool
    delays: Delays


@dataclass(slots=True, frozen=True, kw_only=True)
class Config:
    """
    Holds application configuration.
    """

    browser_config: BrowserConfig


def _load_yaml(file_path: str) -> dict[str, Any]:
    """
    Loads a YAML file and returns its content as a dictionary.
    :param file_path: Path to the YAML file.
    :raises ValueError: If the file cannot be found or parsed.
    :return: Dictionary representation of the YAML file.
    """
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ValueError(f"Configuration file '{file_path}' not found")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


def _require_field(data: dict[str, Any], field_name: str, context: str) -> Any:
    """
    Ensures that a required field is present in the data dictionary.
    :param data: Data dictionary.
    :param field_name: Name of the required field.
    :param context: Context for error messages.
    :raises ValueError: If the required field is missing.
    :return: Value of the required field.
    """
    if field_name not in data or data.get(field_name) is None:
        raise ValueError(f"Missing required field '{field_name}' in {context}")
    return data[field_name]


def _load_browser_config(raw_config: dict[str, Any]) -> BrowserConfig:
    """
    Loads browser configuration from the raw configuration dictionary.
    :param raw_config: Raw configuration dictionary.
    :raises ValueError: If required fields are missing or invalid.
    :return: Browser configuration.
    """
    browser_options = raw_config.get("browser_options")
    if not browser_options or not isinstance(browser_options, dict):
        raise ValueError(
            "Missing or invalid 'browser_options' section in configuration"
        )

    headless = _require_field(browser_options, "headless", "browser_options")
    delay_profile_name = _require_field(
        browser_options, "delay_profile", "browser_options"
    ).upper()

    try:
        delay_profile = DelayProfile[delay_profile_name]
    except KeyError:
        raise ValueError(f"Invalid delay profile: {delay_profile_name}")

    delays = Delays(delay_profile)
    return BrowserConfig(headless=headless, delays=delays)


def load_config_from_yaml(file_path: str = "config.yml") -> Config:
    """
    Loads application configuration from a YAML file.
    :param file_path: Path to the YAML configuration file.
    :raises ValueError: If the configuration is invalid or missing required fields.
    :return: Application configuration.
    """
    raw_config = _load_yaml(file_path)
    browser_config = _load_browser_config(raw_config)

    return Config(
        browser_config=browser_config,
    )
