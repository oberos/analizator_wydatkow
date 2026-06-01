from .bills import PREDEFINED_BILLS as PREDEFINED_BILLS
from .clothing_and_footwear import PREDEFINED_CLOTHING_AND_FOOTWEAR as PREDEFINED_CLOTHING_AND_FOOTWEAR
from .groceries import PREDEFINED_GROCERIES as PREDEFINED_GROCERIES
from .health import PREDEFINED_HEALTH as PREDEFINED_HEALTH
from .restaurants import PREDEFINED_RESTAURANTS as PREDEFINED_RESTAURANTS
from .transport import PREDEFINED_TRANSPORT as PREDEFINED_TRANSPORT

PREDEFINED_CATEGORY_GROUPS = {
    "Finance": [],
    "Bills": PREDEFINED_BILLS,
    "Food and Household Chemicals": PREDEFINED_GROCERIES,
    "Transportation": PREDEFINED_TRANSPORT,
    "Savings": [],
    "Health": PREDEFINED_HEALTH,
    "Beauty": [],
    "Clothing and Footwear": PREDEFINED_CLOTHING_AND_FOOTWEAR,
    "Sports": [],
    "Restaurants": PREDEFINED_RESTAURANTS,
    "Recreation": [],
    "Home": [],
}
