from typing import Self

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES


class PredefinedCategorySeedingTests(TestCase):
    def test_new_user_gets_current_predefined_categories(self: Self) -> None:
        user = get_user_model().objects.create_user(username="seed-user")

        category_names = set(Category.objects.filter(user=user).values_list("name", flat=True))
        category_colors = set(Category.objects.filter(user=user).values_list("color", flat=True))

        self.assertEqual(category_names, set(PREDEFINED_CATEGORIES))
        self.assertIn("Unknown", category_names)
        self.assertNotIn("", category_colors)
        self.assertNotIn(None, category_colors)


class CategoryOwnershipURLTests(TestCase):
    def setUp(self: Self) -> None:
        self.user = get_user_model().objects.create_user(username="category-owner-user")
        self.other_user = get_user_model().objects.create_user(username="category-foreign-user")
        self.client.force_login(self.user)
        self.foreign_category = Category.objects.create(user=self.other_user, name="Foreign private category")

    def test_edit_url_returns_404_for_foreign_category(self: Self) -> None:
        response = self.client.get(reverse("categories:edit", kwargs={"pk": self.foreign_category.pk}))

        self.assertEqual(response.status_code, 404)
        self.foreign_category.refresh_from_db()
        self.assertEqual(self.foreign_category.name, "Foreign private category")

    def test_edit_post_returns_404_for_foreign_category(self: Self) -> None:
        response = self.client.post(
            reverse("categories:edit", kwargs={"pk": self.foreign_category.pk}),
            {"name": "Renamed by intruder", "color": "#123456"},
        )

        self.assertEqual(response.status_code, 404)
        self.foreign_category.refresh_from_db()
        self.assertEqual(self.foreign_category.name, "Foreign private category")

    def test_delete_url_returns_404_for_foreign_category(self: Self) -> None:
        response = self.client.post(reverse("categories:delete", kwargs={"pk": self.foreign_category.pk}))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.foreign_category.pk).exists())

    def test_delete_confirm_url_returns_404_for_foreign_category(self: Self) -> None:
        response = self.client.get(reverse("categories:delete", kwargs={"pk": self.foreign_category.pk}))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.foreign_category.pk).exists())


class CategoryAuthContractTests(TestCase):
    def setUp(self: Self) -> None:
        self.user = get_user_model().objects.create_user(username="category-auth-user")
        self.category = Category.objects.create(user=self.user, name="Auth category")

    def test_category_list_redirects_anonymous_user_to_login(self: Self) -> None:
        response = self.client.get(reverse("categories:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('categories:list')}")

    def test_category_create_redirects_anonymous_user_to_login(self: Self) -> None:
        response = self.client.post(reverse("categories:create"), {"name": "New category"})
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('categories:create')}")

    def test_category_edit_redirects_anonymous_user_to_login(self: Self) -> None:
        edit_url = reverse("categories:edit", kwargs={"pk": self.category.pk})
        response = self.client.post(edit_url, {"name": "Renamed category"})
        self.assertRedirects(response, f"{reverse('login')}?next={edit_url}")

    def test_category_delete_redirects_anonymous_user_to_login(self: Self) -> None:
        delete_url = reverse("categories:delete", kwargs={"pk": self.category.pk})
        response = self.client.post(delete_url)
        self.assertRedirects(response, f"{reverse('login')}?next={delete_url}")
