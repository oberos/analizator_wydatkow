"""Seed predefined merchant-to-category mappings for existing users."""

from django.db import migrations

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


def seed_predefined_mappings(apps, schema_editor):
    """Create predefined merchant mappings for all existing users."""
    User = apps.get_model("auth", "User")
    Category = apps.get_model("categories", "Category")
    MerchantCategoryMapping = apps.get_model("transactions", "MerchantCategoryMapping")

    for user in User.objects.all():
        # Build a dict of category name -> category object for this user
        user_categories = {cat.name: cat for cat in Category.objects.filter(user=user)}

        mappings_to_create = []
        for merchant, category_name in PREDEFINED_MAPPINGS.items():
            category = user_categories.get(category_name)
            if category:
                mappings_to_create.append(
                    MerchantCategoryMapping(
                        user=user,
                        normalized_merchant=merchant,
                        category=category,
                    )
                )

        MerchantCategoryMapping.objects.bulk_create(
            mappings_to_create,
            ignore_conflicts=True,
        )


def reverse_seed_predefined_mappings(apps, schema_editor):
    """No-op reverse migration - don't delete user data."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0002_seed_unknown_category"),
    ]

    operations = [
        migrations.RunPython(seed_predefined_mappings, reverse_seed_predefined_mappings),
    ]
