from collections import defaultdict
from typing import Sequence

import gspread
from gspread.utils import rowcol_to_a1
from loguru import logger

from golden_butterfly_updater.portfolio_updater.portfolio_updater import (
    PortfolioUpdater,
)
from golden_butterfly_updater.scraper.asset import Asset, AssetType

_TYPE_MAPPING = {
    AssetType.CASH: "Cash",
    AssetType.LONG_TERM_TREASURY: "Long-Term Treasury",
    AssetType.GOLD: "Gold",
    AssetType.SMALL_CAP_STOCKS: "Small-Cap",
    AssetType.LARGE_CAP_STOCKS: "Large-Cap",
}
"""Mapping from AssetType to Google Sheets labels."""

_DEDUCTION_LABELS = [
    "Emergency Fund",
    "Short-Term Expenses",
]
"""Labels in the sheet that act as deductions from the Total Cash."""

_LABEL_COLUMN_INDEX = 1
"""Column index in the Google Sheet for labels (Asset Types and Deductions) (1-indexed)."""

_DEDUCTION_VALUE_COLUMN_INDEX = 2
"""Column index where the deduction values are located (1-indexed)."""

_CURRENT_VALUE_COLUMN_INDEX = 3
"""Column index in the Google Sheet for current values (1-indexed)."""


class GooglePortfolioUpdater(PortfolioUpdater):
    """
    Implementation of PortfolioUpdater for Google Sheets using gspread.
    """

    _credentials_path: str
    """Path to the Google Service Account credentials JSON file."""
    _sheet_name: str
    """Name of the Google Sheet to update."""
    _client: gspread.Client | None
    """gspread client instance."""
    _worksheet: gspread.Worksheet | None
    """Worksheet instance."""

    def __init__(self, credentials_path: str, sheet_name: str):
        self._credentials_path = credentials_path
        self._sheet_name = sheet_name
        self._client = None
        self._worksheet = None

    def _get_worksheet(self) -> gspread.Worksheet:
        """
        Lazily initializes and returns the worksheet instance.
        :return: gspread.Worksheet instance.
        """
        if self._worksheet is None:
            try:
                self._client = gspread.service_account(filename=self._credentials_path)
                sh = self._client.open(self._sheet_name)
                self._worksheet = sh.get_worksheet(0)
            except Exception as e:
                logger.error(f"Failed to connect to Google Sheets: {e}")
                raise e
        return self._worksheet

    def _get_deduction_cell_refs(
        self, label_column_values: Sequence[str | int | float | None]
    ) -> list[str]:
        """
        Finds the A1 notation references for the deduction values.
        It assumes the label is in _LABEL_COLUMN_INDEX and the value
        in _DEDUCTION_VALUE_COLUMN_INDEX.

        :param label_column_values: List of strings from the label column.
        :return: List of cell references (e.g., ['B2', 'B5']).
        """
        refs = []
        for label in _DEDUCTION_LABELS:
            try:
                row_index = label_column_values.index(label) + 1
                # Convert to A1 notation (e.g., row 2, col 2 -> "B2")
                a1_ref = rowcol_to_a1(row_index, _DEDUCTION_VALUE_COLUMN_INDEX)
                refs.append(a1_ref)
                logger.debug(f"Found deduction '{label}' at {a1_ref}")
            except ValueError:
                logger.warning(
                    f"Deduction label '{label}' not found in the sheet. Ignoring."
                )
        return refs

    def update_portfolio(self, assets: list[Asset]) -> None:
        logger.info("Starting Google Sheets update...")

        aggregated_data: dict[AssetType, float] = defaultdict(float)
        for asset in assets:
            aggregated_data[asset.asset_type] += asset.amount

        ws = self._get_worksheet()

        label_column_values = ws.col_values(_LABEL_COLUMN_INDEX)
        deduction_refs = self._get_deduction_cell_refs(label_column_values)
        updates_made = 0

        for asset_type, total_value in aggregated_data.items():
            sheet_label = _TYPE_MAPPING.get(asset_type)

            if not sheet_label:
                logger.warning(f"No mapping found for asset type: {asset_type}")
                continue

            try:
                row_index = label_column_values.index(sheet_label) + 1

                if asset_type == AssetType.CASH and deduction_refs:
                    # Construct formula: =TOTAL_VALUE - REF1 - REF2
                    formula_str = f"={total_value}"
                    for ref in deduction_refs:
                        formula_str += f" - {ref}"

                    ws.update_cell(row_index, _CURRENT_VALUE_COLUMN_INDEX, formula_str)
                    logger.debug(
                        f"Updated {sheet_label} with formula: {formula_str} (Base: {total_value})"
                    )
                else:
                    ws.update_cell(row_index, _CURRENT_VALUE_COLUMN_INDEX, total_value)
                    logger.debug(f"Updated {sheet_label} with value {total_value}")

                updates_made += 1

            except ValueError:
                logger.error(
                    f"Label '{sheet_label}' not found in the first column of the sheet."
                )
            except Exception as e:
                logger.exception(f"Error updating {sheet_label}: {e}")

        logger.info(f"Google Sheets update completed. {updates_made} rows updated.")
