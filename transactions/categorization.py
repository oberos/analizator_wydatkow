"""Auto-categorization engine for transactions based on merchant mappings."""

import re

from django.contrib.auth.models import AbstractUser

from categories.models import Category

from .csv_parser import ParsedTransaction
from .models import MerchantCategoryMapping


def normalize_merchant(raw_merchant: str) -> str:
    """
    Normalize merchant name for consistent matching.

    Rules:
    - Uppercase
    - Strip leading/trailing whitespace
    - Remove location suffixes (POL, KATOWICE, etc.)
    - Remove store numbers (4936, 1337, etc.)
    - Remove common suffixes (SP.ZO.O, S.A., etc.)

    Example: "JMP S.A. BIEDRONKA 4936  SWIETOCHLO" -> "BIEDRONKA"
    """
    if not raw_merchant:
        return ""

    # Uppercase and strip
    name = raw_merchant.upper().strip()

    # Remove common company suffixes and prefixes
    company_patterns = [
        r"^JMP\s+S\.?A\.?\s+",  # JMP S.A. at start (Biedronka's parent company)
        r"\s+SP\.?\s*Z\.?\s*O\.?\s*O\.?",  # SP. Z O.O., SP.ZO.O, etc.
        r"\s+SP\.?\s*Z\.?\s*O\.?\s*O",
        r"\s+S\.?\s*A\.?",  # S.A.
        r"\s+SP\.?\s*J\.?",  # SP.J.
    ]
    for pattern in company_patterns:
        name = re.sub(pattern, " ", name, flags=re.IGNORECASE)

    # Remove location suffixes (common Polish cities and country codes)
    location_patterns = [
        r"\s+POL\s*$",  # POL at end
        r"\s+POLSKA\s*$",
        r"\s+KATOWICE.*$",
        r"\s+WARSZAWA.*$",
        r"\s+KRAKOW.*$",
        r"\s+WROCLAW.*$",
        r"\s+POZNAN.*$",
        r"\s+GDANSK.*$",
        r"\s+LODZ.*$",
        r"\s+SWIETOCHLOWIC.*$",
        r"\s+RUDA\s+SLASKA.*$",
        r"\s+SLASKA.*$",
        r"\s+\d{2}-\d{3}\s+\w+.*$",  # Postal code + city
    ]
    for pattern in location_patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    # Remove store/branch numbers (digits at end or after store name)
    # Match patterns like "BIEDRONKA 4936", "ZABKA Z0307 K.2"
    name = re.sub(r"\s+\d+\s*$", "", name)  # Numbers at end
    name = re.sub(r"\s+[A-Z]?\d+[A-Z]?\.\d+.*$", "", name)  # Z0307 K.2 pattern
    name = re.sub(r"\s+[A-Z]\d+.*$", "", name)  # Z0307 pattern
    name = re.sub(r"\s+\d{4,}.*$", "", name)  # Long numbers with trailing text

    # Clean up multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name


def categorize_transaction(
    user: AbstractUser,
    raw_merchant: str,
    mappings_cache: dict[str, Category] | None = None,
) -> Category | None:
    """
    Find category for merchant using user's MerchantCategoryMapping.

    Args:
        user: The user whose mappings to use.
        raw_merchant: The raw merchant name from the CSV.
        mappings_cache: Optional pre-loaded dict of normalized_merchant -> Category.

    Returns:
        Category if mapping exists, None otherwise (caller assigns "Unknown").
    """
    normalized = normalize_merchant(raw_merchant)
    if not normalized:
        return None

    if mappings_cache is not None:
        return mappings_cache.get(normalized)

    # Query database for mapping
    try:
        mapping = MerchantCategoryMapping.objects.select_related("category").get(
            user=user, normalized_merchant=normalized
        )
    except MerchantCategoryMapping.DoesNotExist:
        return None
    else:
        return mapping.category


def categorize_transactions(
    user: AbstractUser,
    parsed_transactions: list[ParsedTransaction],
) -> list[tuple[ParsedTransaction, Category | None]]:
    """
    Categorize a batch of transactions efficiently.

    Loads all user's MerchantCategoryMappings once, then matches each transaction.

    Args:
        user: The user whose mappings to use.
        parsed_transactions: List of ParsedTransaction from CSV parser.

    Returns:
        List of (ParsedTransaction, Category or None) tuples.
    """
    # Load all mappings for user in one query
    mappings = MerchantCategoryMapping.objects.filter(user=user).select_related("category")
    mappings_cache: dict[str, Category] = {m.normalized_merchant: m.category for m in mappings}

    results = []
    for tx in parsed_transactions:
        category = categorize_transaction(user, tx.merchant, mappings_cache)
        results.append((tx, category))

    return results
