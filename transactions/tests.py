from django.contrib.auth import get_user_model
from django.test import TestCase

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES

from .categorization import categorize_transaction
from .mappings import PREDEFINED_CATEGORY_GROUPS, PREDEFINED_MAPPINGS
from .models import MerchantCategoryMapping


class PredefinedMappingSeedTests(TestCase):
    def test_predefined_mapping_category_groups_align_with_runtime_taxonomy(self) -> None:
        expected_categories = set(PREDEFINED_CATEGORIES) - {"Unknown"}
        self.assertEqual(set(PREDEFINED_CATEGORY_GROUPS), expected_categories)

    def test_new_user_gets_predefined_mappings_without_missing_categories(self) -> None:
        user = get_user_model().objects.create_user(username="mapping-seed-user")
        user_category_names = set(Category.objects.filter(user=user).values_list("name", flat=True))
        user_mappings = MerchantCategoryMapping.objects.filter(user=user).select_related("category")

        self.assertEqual(user_mappings.count(), len(PREDEFINED_MAPPINGS))
        self.assertTrue(user_mappings.exists())

        for mapping in user_mappings:
            self.assertIn(mapping.category.name, user_category_names)


class CategorizationTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="categorization-user")

    def test_categorize_transaction_matches_representative_merchants(self) -> None:
        test_cases = [
            ("REVOLUT", "Finance"),
            ("NETFLIX", "Bills"),
            (' FHU "AGA"-LEWIATAN 2  Ruda Slaska ', "Food and Household Chemicals"),
            ("ORLEN STACJA NR 100 MIKOLOW - BOR", "Transportation"),
            ("PPK", "Savings"),
            ("APTEKA HYGIEIA SWIETOCHLOWIC POL", "Health"),
            ("ROSSMANN SKLEP 1337 SWIETOCHLOWIC", "Beauty"),
            ("PEPCO", "Clothing and Footwear"),
            ("DECATHLON", "Sports"),
            ("MCDONALDS", "Restaurants"),
            ("MULTIKINO", "Recreation"),
            ("IKEA", "Home"),
            ("Unknown Merchant", None),
            ("SHOPPINGBPARK", None),
        ]

        for raw_merchant, expected_category_name in test_cases:
            category = categorize_transaction(self.user, raw_merchant)
            category_name = category.name if category else None
            self.assertEqual(category_name, expected_category_name)

    def test_categorize_transaction_uses_same_matching_with_cache(self) -> None:
        mappings = MerchantCategoryMapping.objects.filter(user=self.user).select_related("category")
        mappings_cache = {mapping.normalized_merchant: mapping.category for mapping in mappings}

        category = categorize_transaction(
            self.user,
            "CIRCLE K RUDA SLAS RUDA SLLSKA 417",
            mappings_cache,
        )

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Transportation")
