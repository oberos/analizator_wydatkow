from .beauty import PREDEFINED_BEAUTY as PREDEFINED_BEAUTY
from .bills import PREDEFINED_BILLS as PREDEFINED_BILLS
from .clothing_and_footwear import PREDEFINED_CLOTHING_AND_FOOTWEAR as PREDEFINED_CLOTHING_AND_FOOTWEAR
from .finance import PREDEFINED_FINANCE as PREDEFINED_FINANCE
from .groceries import PREDEFINED_GROCERIES as PREDEFINED_GROCERIES
from .health import PREDEFINED_HEALTH as PREDEFINED_HEALTH
from .home import PREDEFINED_HOME as PREDEFINED_HOME
from .recreation import PREDEFINED_RECREATION as PREDEFINED_RECREATION
from .restaurants import PREDEFINED_RESTAURANTS as PREDEFINED_RESTAURANTS
from .savings import PREDEFINED_SAVINGS as PREDEFINED_SAVINGS
from .sports import PREDEFINED_SPORTS as PREDEFINED_SPORTS
from .transport import PREDEFINED_TRANSPORT as PREDEFINED_TRANSPORT

PREDEFINED_CATEGORY_GROUPS = {
    "Finance": PREDEFINED_FINANCE,
    "Bills": PREDEFINED_BILLS,
    "Food and Household Chemicals": PREDEFINED_GROCERIES,
    "Transportation": PREDEFINED_TRANSPORT,
    "Savings": PREDEFINED_SAVINGS,
    "Health": PREDEFINED_HEALTH,
    "Beauty": PREDEFINED_BEAUTY,
    "Clothing and Footwear": PREDEFINED_CLOTHING_AND_FOOTWEAR,
    "Sports": PREDEFINED_SPORTS,
    "Restaurants": PREDEFINED_RESTAURANTS,
    "Recreation": PREDEFINED_RECREATION,
    "Home": PREDEFINED_HOME,
}


def _validate_unique_merchants() -> None:
    merchant_to_category: dict[str, str] = {}
    duplicate_assignments: dict[str, list[str]] = {}

    for category_name, merchants in PREDEFINED_CATEGORY_GROUPS.items():
        for merchant in merchants:
            previous_category = merchant_to_category.get(merchant)
            if previous_category and previous_category != category_name:
                duplicate_assignments.setdefault(merchant, [previous_category]).append(category_name)
                continue
            merchant_to_category[merchant] = category_name

    if duplicate_assignments:
        details = ", ".join(
            f"{merchant} ({' / '.join(categories)})" for merchant, categories in sorted(duplicate_assignments.items())
        )
        raise ValueError(f"Duplicate predefined merchant keys across categories: {details}")


_validate_unique_merchants()

PREDEFINED_MAPPINGS = {
    merchant: category_name for category_name, merchants in PREDEFINED_CATEGORY_GROUPS.items() for merchant in merchants
}
