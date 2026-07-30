"""Models for budget management."""

from collections.abc import Iterable
from decimal import Decimal
from typing import Self

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from categories.models import Category


class Budget(models.Model):
    """A budget period with name, dates, and user ownership."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["user", "start_date"]),
        ]

    def __str__(self: Self) -> str:
        return f"{self.name} ({self.start_date} to {self.end_date})"

    def clean(self: Self) -> None:
        super().clean()

        # Validate start_date <= end_date
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"start_date": "Start date must be on or before end date."})

        # Check for overlapping budgets for the same user
        # Skip overlap check if user is not yet assigned (form validation will handle it)
        if hasattr(self, "user_id") and self.user_id and self.start_date and self.end_date:  # type: ignore[has-type]
            overlapping = Budget.objects.filter(user=self.user).filter(
                Q(start_date__lte=self.end_date) & Q(end_date__gte=self.start_date)
            )
            # Exclude self if this is an update
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError("Budget dates overlap with an existing budget.")

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


class BudgetCategoryAllocation(models.Model):
    """Per-category budget allocation within a budget."""

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budget_allocations",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("budget", "category")

    def __str__(self: Self) -> str:
        return f"{self.budget.name} - {self.category.name}: {self.amount}"

    def clean(self: Self) -> None:
        super().clean()

        # Validate amount >= 0
        if self.amount is not None and self.amount < Decimal("0"):
            raise ValidationError({"amount": "Amount must be zero or positive."})

        # Validate category belongs to same user as budget
        if self.category and self.budget and self.category.user != self.budget.user:
            raise ValidationError({"category": "Selected category must belong to the same user as the budget."})

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
