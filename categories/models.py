import re
from collections.abc import Iterable
from typing import Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from categories.colors import DEFAULT_CATEGORY_COLOR, color_for_category_name

HEX_COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Category(models.Model):
    """A spending category owned by a user."""

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default=DEFAULT_CATEGORY_COLOR)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    class Meta:
        unique_together = ("name", "user")
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self: Self) -> str:
        return self.name

    def clean(self: Self) -> None:
        super().clean()
        if not HEX_COLOR_REGEX.fullmatch(self.color):
            raise ValidationError({"color": "Color must be a valid 6-digit hex value (e.g. #1a2b3c)."})

    def save(
        self: Self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        if not self.color:
            self.color = color_for_category_name(self.name)
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
