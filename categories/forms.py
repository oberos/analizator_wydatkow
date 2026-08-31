from collections import defaultdict
from typing import Any, Self

from django import forms
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from .models import Category

CategoryChoice = tuple[Any, str]
CategoryChoiceGroup = tuple[str, list[CategoryChoice]]


def group_categories_by_parent(categories: QuerySet[Category]) -> list[tuple[Category, list[Category]]]:
    """Group a flat queryset of categories into (top_level, subcategories) pairs.

    Consumes the queryset in a single evaluation and groups in memory, so callers
    render hierarchical dropdowns without a query per parent.
    """
    children: dict[int, list[Category]] = defaultdict(list)
    top_level: list[Category] = []

    for category in categories:
        parent_id: int | None = category.parent_id  # type: ignore[attr-defined]
        if parent_id is None:
            top_level.append(category)
        else:
            children[parent_id].append(category)

    top_level.sort(key=lambda category: category.name)
    for group in children.values():
        group.sort(key=lambda category: category.name)

    return [(parent, children.get(parent.pk, [])) for parent in top_level]


def grouped_category_choices(
    categories: QuerySet[Category],
    empty_label: str | None = None,
) -> list[CategoryChoice | CategoryChoiceGroup]:
    """Build select choices that nest subcategories under their parent's <optgroup>.

    Parents keep their own entry inside the group so either level stays selectable.
    Childless categories render as plain top-level options.
    """
    choices: list[CategoryChoice | CategoryChoiceGroup] = []
    if empty_label is not None:
        choices.append(("", empty_label))

    for parent, subcategories in group_categories_by_parent(categories):
        if subcategories:
            group: list[CategoryChoice] = [(parent.pk, parent.name)]
            group.extend((child.pk, child.name) for child in subcategories)
            choices.append((parent.name, group))
        else:
            choices.append((parent.pk, parent.name))

    return choices


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories with optional parent assignment."""

    class Meta:
        model = Category
        fields = ["name", "color", "parent"]
        widgets = {
            "parent": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self: Self, *args: Any, user: AbstractUser | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        # Bind the owner before validation runs: `user` is not a form field, so without this the
        # model's parent-ownership check compares against an unset user and every subcategory is
        # rejected, and both uniqueness constraints are skipped as referencing an excluded field.
        if user is not None and self.instance.user_id is None:  # type: ignore[attr-defined]
            self.instance.user = user  # type: ignore[assignment]

        parent_field = self.fields["parent"]
        parent_field.required = False
        parent_field.empty_label = "— None (top-level category) —"  # type: ignore[attr-defined]

        queryset = Category.objects.none()
        if user is not None:
            queryset = Category.objects.filter(user=user, parent__isnull=True).order_by("name")
            if self.instance.pk is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
        parent_field.queryset = queryset  # type: ignore[attr-defined]

    def _get_validation_exclusions(self: Self) -> set[str]:
        """Keep `user` in scope for model validation.

        `user` is set in __init__ rather than posted, so without this the name-uniqueness
        constraints are skipped here and raise an uncaught ValidationError from
        Category.save() instead of becoming form errors.

        NOTE: this overrides a private Django API (leading underscore), verified against
        Django 6.0. On a Django upgrade, re-check that `ModelForm._get_validation_exclusions`
        still exists and still returns a mutable set of field names; if it changes, the
        `CategoryFormValidation` tests will fail loudly rather than silently skipping
        uniqueness checks.
        """
        exclusions = super()._get_validation_exclusions()  # type: ignore[attr-defined]
        exclusions.discard("user")
        return exclusions
