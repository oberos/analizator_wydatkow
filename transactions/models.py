from collections.abc import Iterable
from typing import Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from categories.models import Category


class Transaction(models.Model):
    """A bank transaction imported from CSV."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    date = models.DateField()  # Data transakcji
    booking_date = models.DateField(null=True, blank=True)  # Data księgowania
    merchant = models.CharField(max_length=200)  # Dane kontrahenta (raw)
    description = models.CharField(max_length=500)  # Tytuł
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Kwota transakcji
    transaction_number = models.CharField(max_length=50, blank=True)  # Nr transakcji
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    class Meta:
        ordering = ["-date", "-id"]
        unique_together = [("user", "date", "amount", "merchant", "transaction_number")]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category", "-date"]),
        ]

    def __str__(self) -> str:  # noqa: ANN101
        return f"{self.date} {self.merchant} {self.amount}"

    def clean(self: Self) -> None:
        super().clean()
        if self.category is None:
            return
        if self.category.user != self.user:
            raise ValidationError({"category": "Selected category must belong to the same user as the transaction."})

    def save(
        self: Self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class MerchantCategoryMapping(models.Model):
    """Learned association between normalized merchant name and category."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant_mappings",
    )
    normalized_merchant = models.CharField(max_length=200)  # e.g., "BIEDRONKA"
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="merchant_mappings",
    )

    class Meta:
        unique_together = [("user", "normalized_merchant")]

    def __str__(self) -> str:  # noqa: ANN101
        return f"{self.normalized_merchant} -> {self.category.name}"

    def clean(self: Self) -> None:
        super().clean()
        if self.category.user != self.user:
            raise ValidationError(
                {"category": "Selected category must belong to the same user as the merchant mapping."}
            )

    def save(
        self: Self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
