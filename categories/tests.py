from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES


class PredefinedCategorySeedingTests(TestCase):
    def test_new_user_gets_current_predefined_categories(self) -> None:
        user = get_user_model().objects.create_user(username="seed-user")

        category_names = set(Category.objects.filter(user=user).values_list("name", flat=True))

        self.assertEqual(category_names, set(PREDEFINED_CATEGORIES))
        self.assertIn("Unknown", category_names)


class CategoryOwnershipURLTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="category-owner-user")
        self.other_user = get_user_model().objects.create_user(username="category-foreign-user")
        self.client.force_login(self.user)
        self.foreign_category = Category.objects.create(user=self.other_user, name="Foreign private category")

    def test_edit_url_returns_404_for_foreign_category(self) -> None:
        response = self.client.get(reverse("categories:edit", kwargs={"pk": self.foreign_category.pk}))

        self.assertEqual(response.status_code, 404)
        self.foreign_category.refresh_from_db()
        self.assertEqual(self.foreign_category.name, "Foreign private category")

    def test_delete_url_returns_404_for_foreign_category(self) -> None:
        response = self.client.post(reverse("categories:delete", kwargs={"pk": self.foreign_category.pk}))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.foreign_category.pk).exists())
