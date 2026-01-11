import re

PHONE_COUNTRY_CODE_PATTERN = re.compile(r"^\+\d{1,4}$")
"""Pattern that checks for valid phone country codes (e.g., +34, +1)."""

PHONE_NUMBER_PATTERN = re.compile(r"^\d{5,15}$")
"""Pattern that checks for valid phone numbers (5-15 digits)."""

PIN_PATTERN = re.compile(r"^\d{4}$")
"""Pattern that checks for valid 4-digit PINs."""

ISIN_PATTERN = re.compile(r"([A-Z]{2}[A-Z0-9]{9}\d)")
"""Pattern that checks for valid ISINs (2 letters, 9 alphanumeric characters, 1 digit)."""
