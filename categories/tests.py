from typing import Self

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import HttpResponse
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


class SubcategoryCreationViewTests(TestCase):
    """End-to-end view coverage for creating subcategories through the CRUD form."""

    def setUp(self: Self) -> None:
        self.user = get_user_model().objects.create_user(username="subcategory-user", password="pw")  # noqa: S106
        self.client.force_login(self.user)
        Category.objects.filter(user=self.user).delete()
        self.food = Category.objects.create(user=self.user, name="Food", color="#ff0000")

    def _post_create(self: Self, **overrides: object) -> HttpResponse:
        payload: dict[str, object] = {"name": "Groceries", "color": "#6c757d", "parent": self.food.pk}
        payload.update(overrides)
        return self.client.post(reverse("categories:create"), payload)

    def test_subcategory_is_created_through_the_form(self: Self) -> None:
        response = self._post_create()

        self.assertRedirects(response, reverse("categories:list"))
        subcategory = Category.objects.get(user=self.user, name="Groceries")
        self.assertEqual(subcategory.parent, self.food)

    def test_parent_accepts_more_than_one_subcategory(self: Self) -> None:
        self._post_create(name="Groceries")
        self._post_create(name="Restaurants")

        self.assertEqual(self.food.subcategories.count(), 2)  # type: ignore[attr-defined]

    def test_subcategory_inherits_parent_color_when_left_at_default(self: Self) -> None:
        self._post_create()

        self.assertEqual(Category.objects.get(user=self.user, name="Groceries").color, "#ff0000")

    def test_duplicate_top_level_name_is_reported_as_a_form_error(self: Self) -> None:
        response = self._post_create(name="Food", parent="")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You already have a top-level category with this name.")
        self.assertEqual(Category.objects.filter(user=self.user, name="Food").count(), 1)

    def test_duplicate_sibling_name_is_reported_as_a_form_error(self: Self) -> None:
        self._post_create()

        response = self._post_create()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This parent category already has a subcategory with this name.")
        self.assertEqual(self.food.subcategories.count(), 1)  # type: ignore[attr-defined]

    def test_parent_dropdown_excludes_subcategories_and_foreign_categories(self: Self) -> None:
        self._post_create()
        other = get_user_model().objects.create_user(username="subcategory-other")
        Category.objects.create(user=other, name="Foreign")

        form = self.client.get(reverse("categories:create")).context["form"]
        offered = {category.name for category in form.fields["parent"].queryset}

        self.assertIn("Food", offered)
        self.assertNotIn("Groceries", offered)
        self.assertNotIn("Foreign", offered)

    def test_deleting_parent_cascades_to_subcategories(self: Self) -> None:
        self._post_create()

        self.client.post(reverse("categories:delete", kwargs={"pk": self.food.pk}))

        self.assertFalse(Category.objects.filter(user=self.user, name="Groceries").exists())


class CategoryHierarchyModelTests(TestCase):
    """Model-level rules for the one-level category hierarchy."""

    def setUp(self: Self) -> None:
        self.user = get_user_model().objects.create_user(username="hierarchy-user")
        self.other_user = get_user_model().objects.create_user(username="hierarchy-other")
        self.food = Category.objects.get(user=self.user, name="Food and Household Chemicals")
        self.transport = Category.objects.get(user=self.user, name="Transportation")

    def test_subcategory_of_a_subcategory_is_rejected(self: Self) -> None:
        groceries = Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        with self.assertRaises(ValidationError) as ctx:
            Category.objects.create(user=self.user, name="Dairy", parent=groceries)

        self.assertIn("Subcategories cannot have their own subcategories.", ctx.exception.messages)

    def test_category_with_subcategories_cannot_become_a_subcategory(self: Self) -> None:
        Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        self.food.parent = self.transport  # type: ignore[assignment]
        with self.assertRaises(ValidationError) as ctx:
            self.food.save()

        self.assertIn(
            "A category that has subcategories cannot become a subcategory itself.",
            ctx.exception.messages,
        )

    def test_same_subcategory_name_under_different_parents_is_allowed(self: Self) -> None:
        first = Category.objects.create(user=self.user, name="Other", parent=self.food)
        second = Category.objects.create(user=self.user, name="Other", parent=self.transport)

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Category.objects.filter(user=self.user, name="Other").count(), 2)

    def test_subcategory_may_share_a_name_with_a_top_level_category(self: Self) -> None:
        subcategory = Category.objects.create(user=self.user, name="Transportation", parent=self.food)

        self.assertEqual(subcategory.parent, self.food)
        self.assertTrue(Category.objects.filter(user=self.user, name="Transportation", parent__isnull=True).exists())

    def test_duplicate_sibling_name_is_rejected(self: Self) -> None:
        Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        with self.assertRaises(ValidationError) as ctx:
            Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        self.assertIn("This parent category already has a subcategory with this name.", ctx.exception.messages)

    def test_parent_owned_by_another_user_is_rejected(self: Self) -> None:
        foreign_parent = Category.objects.get(user=self.other_user, name="Food and Household Chemicals")

        with self.assertRaises(ValidationError) as ctx:
            Category.objects.create(user=self.user, name="Groceries", parent=foreign_parent)

        self.assertIn("Selected parent category must belong to the same user.", ctx.exception.messages)

    def test_deleting_a_parent_cascades_to_its_subcategories(self: Self) -> None:
        subcategory = Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        self.food.delete()

        self.assertFalse(Category.objects.filter(pk=subcategory.pk).exists())

    def test_subcategory_inherits_parent_color_when_left_at_default(self: Self) -> None:
        self.food.color = "#123456"
        self.food.save()

        subcategory = Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        self.assertEqual(subcategory.color, "#123456")

    def test_explicit_subcategory_color_is_preserved(self: Self) -> None:
        self.food.color = "#123456"
        self.food.save()

        subcategory = Category.objects.create(
            user=self.user,
            name="Groceries",
            parent=self.food,
            color="#abcdef",
        )

        self.assertEqual(subcategory.color, "#abcdef")

    def test_is_subcategory_reflects_parent_assignment(self: Self) -> None:
        subcategory = Category.objects.create(user=self.user, name="Groceries", parent=self.food)

        self.assertTrue(subcategory.is_subcategory)
        self.assertFalse(self.food.is_subcategory)
