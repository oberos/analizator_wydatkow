from django.conf import settings
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

    def __str__(self) -> str:
        return f"{self.date} {self.merchant} {self.amount}"


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

    def __str__(self) -> str:
        return f"{self.normalized_merchant} -> {self.category.name}"
