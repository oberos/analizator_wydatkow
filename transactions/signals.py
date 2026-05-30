from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from categories.models import Category

from .models import MerchantCategoryMapping

User = get_user_model()

PREDEFINED_MAPPINGS = {
    # Groceries
    "BIEDRONKA": "Groceries",
    "LIDL": "Groceries",
    "KAUFLAND": "Groceries",
    "AUCHAN": "Groceries",
    "CARREFOUR": "Groceries",
    "ZABKA": "Groceries",
    "LEWIATAN": "Groceries",
    "DINO": "Groceries",
    "NETTO": "Groceries",
    "INTERMARCHE": "Groceries",
    "STOKROTKA": "Groceries",
    "POLO MARKET": "Groceries",
    "FRESHMARKET": "Groceries",
    "DELIKATESY": "Groceries",
    "PIEKARNIA": "Groceries",
    "RZEZNIK": "Groceries",
    "ALDI": "Groceries",
    # Transport / Fuel
    "ORLEN": "Transport",
    "BP": "Transport",
    "SHELL": "Transport",
    "CIRCLE K": "Transport",
    "LOTOS": "Transport",
    "MOYA": "Transport",
    "AMIC": "Transport",
    "BOLT": "Transport",
    "UBER": "Transport",
    "FREENOW": "Transport",
    "FLIXBUS": "Transport",
    "PKP": "Transport",
    "INTERCITY": "Transport",
    "METROPOLIA": "Transport",
    "JAKDOJADE": "Transport",
    # Restaurants / Fast food
    "MCDONALDS": "Entertainment",
    "KFC": "Entertainment",
    "BURGER KING": "Entertainment",
    "PIZZA HUT": "Entertainment",
    "STARBUCKS": "Entertainment",
    "COSTA COFFEE": "Entertainment",
    "SUBWAY": "Entertainment",
    "KEBAB": "Entertainment",
    "BISTRO": "Entertainment",
    "RESTAURACJA": "Entertainment",
    # Health / Pharmacy
    "ROSSMANN": "Health",
    "HEBE": "Health",
    "DROGERIA": "Health",
    "APTEKA": "Health",
    "SUPERPHARM": "Health",
    "ZIKO": "Health",
    # Bills / Subscriptions
    "NETFLIX": "Bills",
    "SPOTIFY": "Bills",
    "YOUTUBE": "Bills",
    "PLAY": "Bills",
    "ORANGE": "Bills",
    "T-MOBILE": "Bills",
    "PLUS": "Bills",
    "UPC": "Bills",
    "VECTRA": "Bills",
    "PGE": "Bills",
    "TAURON": "Bills",
    "ENEA": "Bills",
}


@receiver(post_save, sender=User)
def create_predefined_mappings(
    sender: type, instance: User, created: bool, **kwargs  # noqa: ANN003, ARG001
) -> None:
    """Create predefined merchant mappings for newly registered users."""
    if created:
        # Need to wait for categories to be created first (by categories.signals)
        # So we query the categories that were just created
        user_categories = {cat.name: cat for cat in Category.objects.filter(user=instance)}

        mappings_to_create = []
        for merchant, category_name in PREDEFINED_MAPPINGS.items():
            category = user_categories.get(category_name)
            if category:
                mappings_to_create.append(
                    MerchantCategoryMapping(
                        user=instance,
                        normalized_merchant=merchant,
                        category=category,
                    )
                )

        MerchantCategoryMapping.objects.bulk_create(
            mappings_to_create,
            ignore_conflicts=True,
        )
