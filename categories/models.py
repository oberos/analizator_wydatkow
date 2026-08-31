import re
from collections.abc import Iterable
from typing import Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from categories.colors import DEFAULT_CATEGORY_COLOR, color_for_category_name

HEX_COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Category(models.Model):
    """A spending category or subcategory owned by a user."""

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default=DEFAULT_CATEGORY_COLOR)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user"],
                condition=models.Q(parent__isnull=True),
                name="unique_top_level_category_name_per_user",
                violation_error_message="You already have a top-level category with this name.",
            ),
            models.UniqueConstraint(
                fields=["name", "user", "parent"],
                name="unique_subcategory_name_per_parent",
                violation_error_message="This parent category already has a subcategory with this name.",
            ),
        ]

    def __str__(self: Self) -> str:
        return self.name

    @property
    def is_subcategory(self: Self) -> bool:
        return self.parent_id is not None  # type: ignore[attr-defined]

    def clean(self: Self) -> None:
        super().clean()
        if not HEX_COLOR_REGEX.fullmatch(self.color):
            raise ValidationError({"color": "Color must be a valid 6-digit hex value (e.g. #1a2b3c)."})

        parent: Category | None = self.parent  # type: ignore[assignment]
        if parent is None:
            return

        if self.pk is not None and parent.pk == self.pk:
            raise ValidationError({"parent": "A category cannot be its own parent."})
        if parent.user_id != self.user_id:  # type: ignore[attr-defined]
            raise ValidationError({"parent": "Selected parent category must belong to the same user."})
        if parent.parent_id is not None:  # type: ignore[attr-defined]
            raise ValidationError({"parent": "Subcategories cannot have their own subcategories."})
        if self.pk is not None and self.subcategories.exists():  # type: ignore[attr-defined]
            raise ValidationError({"parent": "A category that has subcategories cannot become a subcategory itself."})

    def save(
        self: Self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        parent: Category | None = self.parent  # type: ignore[assignment]
        if self._state.adding and parent is not None and self.color == DEFAULT_CATEGORY_COLOR:
            self.color = parent.color
        if not self.color:
            self.color = color_for_category_name(self.name)
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
