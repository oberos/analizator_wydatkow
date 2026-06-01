from django.contrib.auth import get_user_model
from django.test import TestCase

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES


class PredefinedCategorySeedingTests(TestCase):
    def test_new_user_gets_current_predefined_categories(self) -> None:
        user = get_user_model().objects.create_user(username="seed-user")

        category_names = set(Category.objects.filter(user=user).values_list("name", flat=True))

        self.assertEqual(category_names, set(PREDEFINED_CATEGORIES))
        self.assertIn("Unknown", category_names)
