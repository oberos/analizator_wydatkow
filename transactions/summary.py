"""Summary helpers for transaction reporting."""

from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import Abs, Coalesce

from .models import Transaction


def get_user_category_summary(
    user: AbstractUser,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, object]]:
    """Return per-category totals and counts for one user."""
    queryset = Transaction.objects.filter(user=user)
    if start_date is not None:
        queryset = queryset.filter(date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(date__lte=end_date)

    summary = (
        queryset.annotate(category_name=Coalesce("category__name", Value("Uncategorized")))
        .values("category_name")
        .annotate(
            total_amount=Coalesce(
                Sum(
                    Case(
                        When(amount__lt=0, then=Abs(F("amount"))),
                        When(amount__gt=0, then=-F("amount")),
                        default=Value(0),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                ),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            transaction_count=Count("id"),
        )
        .order_by("category_name")
    )
    return list(summary)
