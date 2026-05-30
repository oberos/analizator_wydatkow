"""ING Poland CSV parser for bank transaction imports."""

import csv
import re
from dataclasses import dataclass
from datetime import date as datetime_date
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CSVParseError(Exception):
    """Raised when CSV parsing fails with user-friendly message."""

    def __init__(self, line_number: int, message: str) -> None:
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


@dataclass
class ParsedTransaction:
    """A transaction parsed from ING CSV."""

    date: datetime_date
    booking_date: datetime_date | None
    merchant: str
    description: str
    amount: Decimal
    transaction_number: str


def _decode_content(file_content: bytes) -> str:
    """Decode CSV content trying multiple encodings."""
    encodings = ["windows-1250", "utf-8-sig", "utf-8"]

    for encoding in encodings:
        try:
            return file_content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise CSVParseError(0, "Could not decode file. Expected Windows-1250 or UTF-8 encoding.")


def _find_header_and_footer(lines: list[str]) -> tuple[int, int]:
    """Find the header row and footer row indices."""
    header_idx = None
    footer_idx = len(lines)

    for i, line in enumerate(lines):
        if '"Data transakcji"' in line or line.startswith("Data transakcji"):
            header_idx = i
        if "Dokument ma charakter informacyjny" in line:
            footer_idx = i
            break

    if header_idx is None:
        raise CSVParseError(0, "Could not find header row. Expected 'Data transakcji' column.")

    return header_idx, footer_idx


def _parse_date(date_str: str, line_number: int, field_name: str) -> datetime_date:
    """Parse a date string in YYYY-MM-DD format."""
    date_str = date_str.strip()
    if not date_str:
        raise CSVParseError(line_number, f"Missing {field_name}")

    # Handle both YYYY-MM-DD and YYYYMMDD formats
    if len(date_str) == 8 and date_str.isdigit():
        date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    parts = date_str.split("-")
    if len(parts) != 3:
        raise CSVParseError(line_number, f"Invalid {field_name} format: '{date_str}'")

    try:
        return datetime_date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError) as e:
        raise CSVParseError(line_number, f"Invalid {field_name} format: '{date_str}'") from e


def _parse_optional_date(date_str: str, line_number: int, field_name: str) -> datetime_date | None:
    """Parse an optional date string."""
    date_str = date_str.strip()
    if not date_str:
        return None
    return _parse_date(date_str, line_number, field_name)


def _parse_amount(amount_str: str, line_number: int) -> Decimal:
    """Parse amount string with comma decimal separator."""
    amount_str = amount_str.strip()
    if not amount_str:
        raise CSVParseError(line_number, "Missing amount")

    # Remove spaces (thousands separator) and replace comma with dot
    amount_str = amount_str.replace(" ", "").replace(",", ".")

    try:
        return Decimal(amount_str)
    except InvalidOperation as e:
        raise CSVParseError(line_number, f"Invalid amount format: '{amount_str}'") from e


def _clean_text(text: str) -> str:
    """Clean text by stripping whitespace and quotes."""
    text = text.strip()
    # Remove surrounding quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.strip()


def _clean_transaction_number(tx_number: str) -> str:
    """Clean transaction number by removing apostrophes and extra whitespace."""
    return tx_number.strip().strip("'").strip()


def _get_amount_from_row(row: list[str], header_indices: dict[str, int], line_number: int) -> Decimal:
    """Get amount from row, trying multiple possible columns."""
    # Primary amount column
    amount_col = "Kwota transakcji (waluta rachunku)"
    if amount_col in header_indices:
        amount_str = row[header_indices[amount_col]].strip()
        if amount_str:
            return _parse_amount(amount_str, line_number)

    # Fallback columns
    fallback_cols = ["Kwota blokady/zwolnienie blokady", "Kwota płatności w walucie"]
    for col in fallback_cols:
        if col in header_indices:
            amount_str = row[header_indices[col]].strip()
            if amount_str:
                return _parse_amount(amount_str, line_number)

    raise CSVParseError(line_number, "No valid amount found in any amount column")


def _is_data_row(row: list[str], header_indices: dict[str, int]) -> bool:
    """Check if a row is a valid data row (not metadata or empty)."""
    # Skip empty rows
    if not row or all(not cell.strip() for cell in row):
        return False

    date_col_index = header_indices.get("Data transakcji")
    if date_col_index is None or date_col_index >= len(row):
        return False

    date_cell = row[date_col_index].strip()
    return bool(date_cell and re.match(r"^\d{4}-\d{2}-\d{2}$", date_cell))


def _parse_row(row: list[str], header_indices: dict[str, int], row_num: int) -> ParsedTransaction:
    """Parse a single CSV row into a ParsedTransaction."""
    # Parse date (required)
    date_val = _parse_date(row[header_indices["Data transakcji"]], row_num, "transaction date")

    # Parse booking date (optional)
    booking_date_val = None
    if "Data księgowania" in header_indices and header_indices["Data księgowania"] < len(row):
        booking_date_val = _parse_optional_date(row[header_indices["Data księgowania"]], row_num, "booking date")

    # Parse merchant
    merchant = _clean_text(row[header_indices["Dane kontrahenta"]])

    # Parse description
    description = _clean_text(row[header_indices["Tytuł"]])

    # Parse amount
    amount = _get_amount_from_row(row, header_indices, row_num)

    # Parse transaction number (optional)
    tx_number = ""
    if "Nr transakcji" in header_indices and header_indices["Nr transakcji"] < len(row):
        tx_number = _clean_transaction_number(row[header_indices["Nr transakcji"]])

    return ParsedTransaction(
        date=date_val,
        booking_date=booking_date_val,
        merchant=merchant,
        description=description,
        amount=amount,
        transaction_number=tx_number,
    )


def parse_ing_csv(file_content: bytes) -> list[ParsedTransaction]:
    """
    Parse ING Poland CSV export.

    Args:
        file_content: Raw bytes of the CSV file.

    Returns:
        List of ParsedTransaction dataclasses.

    Raises:
        CSVParseError: With line number and message on validation failure.
    """
    # Decode content
    content = _decode_content(file_content)
    lines = content.splitlines()

    # Find header and footer
    header_idx, footer_idx = _find_header_and_footer(lines)

    # Extract data section
    data_section = "\n".join(lines[header_idx:footer_idx])

    # Parse CSV
    reader = csv.reader(StringIO(data_section), delimiter=";", quotechar='"')

    # Get header row and build column index map
    header_row = next(reader)
    header_indices = {_clean_text(col): i for i, col in enumerate(header_row)}

    # Required columns
    required_cols = ["Data transakcji", "Dane kontrahenta", "Tytuł"]
    for col in required_cols:
        if col not in header_indices:
            raise CSVParseError(header_idx + 1, f"Missing required column: '{col}'")

    transactions = []
    for row_num, row in enumerate(reader, start=header_idx + 2):  # +2 for 1-indexed + header row
        if not _is_data_row(row, header_indices):
            continue

        try:
            transactions.append(_parse_row(row, header_indices, row_num))
        except CSVParseError:
            raise
        except (IndexError, KeyError) as e:
            raise CSVParseError(row_num, f"Row has missing or malformed data: {e}") from e

    return transactions
