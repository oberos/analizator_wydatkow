from typing import Any, Self

from django import forms
from django.contrib.auth.models import AbstractUser

from .models import Category


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
        # `user` is set in __init__ rather than posted, so keep it in scope for model validation;
        # otherwise the name-uniqueness constraints are skipped here and raise an uncaught
        # ValidationError from Category.save() instead of becoming form errors.
        exclusions = super()._get_validation_exclusions()  # type: ignore[attr-defined]
        exclusions.discard("user")
        return exclusions
