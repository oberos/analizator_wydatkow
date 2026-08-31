"""Summary helpers for transaction reporting."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import Abs, Coalesce

from categories.colors import DEFAULT_CATEGORY_COLOR
from categories.models import Category

from .models import Transaction

UNCATEGORIZED_LABEL = "Uncategorized"


def _spending_expression() -> Case:
    """Return the signed-amount expression treating outflows as positive spending."""
    return Case(
        When(amount__lt=0, then=Abs(F("amount"))),
        When(amount__gt=0, then=-F("amount")),
        default=Value(0),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _summary_row(
    category_id: int | None,
    name: str,
    color: str,
    total_amount: Decimal,
    transaction_count: int,
) -> dict[str, Any]:
    return {
        "category_id": category_id,
        "category_name": name,
        "category_color": color,
        "total_amount": total_amount,
        "transaction_count": transaction_count,
        "subcategories": [],
    }


def get_user_category_summary(
    user: AbstractUser,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return per-category totals for one user, rolled up to top-level categories.

    Each returned row is a top-level category (or Uncategorized) whose ``total_amount``
    and ``transaction_count`` include its own transactions plus those of all its
    subcategories. Subcategories that have spending appear as same-shaped rows under
    the parent's ``subcategories`` key, each carrying only its own totals.

    Totals come from one grouped aggregation and one category query; the tree is
    assembled in memory so the query count stays constant as subcategories grow.
    """
    queryset = Transaction.objects.filter(user=user)
    if start_date is not None:
        queryset = queryset.filter(date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(date__lte=end_date)

    aggregated = queryset.values("category_id").annotate(
        total_amount=Coalesce(
            Sum(_spending_expression()),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        transaction_count=Count("id"),
    )
    totals: dict[int | None, tuple[Decimal, int]] = {
        row["category_id"]: (row["total_amount"], row["transaction_count"]) for row in aggregated
    }

    zero = Decimal("0")
    rows_by_id: dict[int, dict[str, Any]] = {}
    children_by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    top_level_ids: list[int] = []

    for category in Category.objects.filter(user=user).select_related("parent"):
        own_total, own_count = totals.get(category.pk, (zero, 0))
        row = _summary_row(category.pk, category.name, category.color, own_total, own_count)
        rows_by_id[category.pk] = row

        parent_id: int | None = category.parent_id  # type: ignore[attr-defined]
        if parent_id is None:
            top_level_ids.append(category.pk)
        else:
            children_by_parent[parent_id].append(row)

    summary: list[dict[str, Any]] = []

    for category_id in top_level_ids:
        row = rows_by_id[category_id]
        children = sorted(children_by_parent.get(category_id, []), key=lambda child: child["category_name"])

        # Roll every child's spending into the parent, but only surface children that
        # actually have transactions so the breakdown stays free of empty rows.
        for child in children:
            row["total_amount"] += child["total_amount"]
            row["transaction_count"] += child["transaction_count"]
            if child["transaction_count"]:
                row["subcategories"].append(child)

        if row["transaction_count"]:
            summary.append(row)

    uncategorized_total, uncategorized_count = totals.get(None, (zero, 0))
    if uncategorized_count:
        summary.append(
            _summary_row(
                None,
                UNCATEGORIZED_LABEL,
                DEFAULT_CATEGORY_COLOR,
                uncategorized_total,
                uncategorized_count,
            )
        )

    summary.sort(key=lambda row: row["category_name"])
    return summary


def flatten_category_summary(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten a nested summary into parent-then-children document order."""
    flattened: list[dict[str, Any]] = []
    for row in summary:
        flattened.append(row)
        flattened.extend(row["subcategories"])
    return flattened
