"""Summary helpers for budget comparison and reporting."""

from decimal import Decimal
from datetime import date
from typing import Any

from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Abs, Coalesce

from budgets.models import Budget
from categories.colors import DEFAULT_CATEGORY_COLOR
from categories.forms import group_categories_by_parent
from categories.models import Category
from transactions.models import Transaction
from transactions.summary import flatten_category_summary, get_user_category_summary


def _category_display_order(budget: Budget) -> dict[int, int]:
    """Map every category the user owns to its parent-then-children display index.

    Built from the full category tree rather than only categories with spending, so a
    budgeted-but-unspent category still sorts beneath its own parent instead of being
    stranded at the end of the table under an unrelated row.
    """
    categories = Category.objects.filter(user=budget.user).order_by("name")

    order: dict[int, int] = {}
    for parent, subcategories in group_categories_by_parent(categories):
        order[parent.pk] = len(order)
        for subcategory in subcategories:
            order[subcategory.pk] = len(order)
    return order


def _resolve_status(budgeted_amount: Decimal, actual_amount: Decimal, difference: Decimal) -> str:
    """Classify an allocation as under, over, or close to its budget."""
    if budgeted_amount > 0:
        ratio = abs(difference / budgeted_amount)
        if ratio < Decimal("0.10"):
            return "close"
        return "over" if difference < 0 else "under"
    # Zero budget: any spending is over
    return "over" if actual_amount > 0 else "under"


def _budget_excluded_category_ids(user: Any) -> set[int]:
    """Return category ids whose transactions must be excluded from budget comparisons."""
    excluded: set[int] = set()

    for category in Category.objects.filter(user=user).select_related("parent"):
        current: Category | None = category
        while current is not None:
            if current.is_income or current.is_irrelevant:
                excluded.add(category.pk)
                break
            current = current.parent

    return excluded


def _expense_totals_for_budget(
    user: Any,
    start_date: date | None,
    end_date: date | None,
) -> dict[int | None, Decimal]:
    """Return total outflows per category for budget comparison, excluding flagged categories."""
    queryset = Transaction.objects.filter(user=user)
    if start_date is not None:
        queryset = queryset.filter(date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(date__lte=end_date)

    category_lookup = {
        category.pk: category for category in Category.objects.filter(user=user).select_related("parent")
    }
    excluded_category_ids = _budget_excluded_category_ids(user)

    aggregated = (
        queryset.filter(amount__lt=0)
        .values("category_id")
        .annotate(
            total_amount=Coalesce(
                Sum(Abs(F("amount"))),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    )

    totals: dict[int | None, Decimal] = {}

    for row in aggregated:
        total_amount = row["total_amount"] or Decimal("0")
        category_id = row["category_id"]

        if category_id is None:
            totals[None] = totals.get(None, Decimal("0")) + total_amount
            continue

        if category_id in excluded_category_ids:
            continue

        current = category_lookup.get(category_id)
        while current is not None:
            if current.is_income or current.is_irrelevant:
                break
            totals[current.pk] = totals.get(current.pk, Decimal("0")) + total_amount
            current = current.parent

    return totals


def get_budget_comparison(budget: Budget) -> list[dict[str, Any]]:
    """
    Merge budget allocations with actual transaction summary for comparison.

    Returns a list of dicts with keys:
    - category_name: str
    - category_color: str
    - budgeted_amount: Decimal
    - actual_amount: Decimal
    - difference: Decimal (positive = under budget, negative = over budget)
    - status: str ('under' | 'over' | 'close')

    Allocations may target a top-level category or a subcategory. Each row is compared
    against that same category's own actual total, which for a top-level category is
    rolled up across its subcategories. Rows are ordered parent-then-children.

    Status logic:
    - 'close': abs(difference / budgeted) < 0.10 and budgeted > 0
    - 'over': difference < 0
    - 'under': otherwise
    """
    # Get actual spending for the budget period
    actual_summary = get_user_category_summary(
        user=budget.user,
        start_date=budget.start_date,
        end_date=budget.end_date,
    )

    excluded_category_ids = _budget_excluded_category_ids(budget.user)

    # Key by category id: names are only unique per parent, so a name-keyed lookup
    # would collide between subcategories sharing a name under different parents.
    ordered_rows = [
        row for row in flatten_category_summary(actual_summary) if row["category_id"] not in excluded_category_ids
    ]
    actual_by_category_id = _expense_totals_for_budget(budget.user, budget.start_date, budget.end_date)
    top_level_category_ids = {
        row["category_id"] for row in actual_summary if row["category_id"] not in excluded_category_ids
    }
    # Ordered from the full category tree so zero-spend allocations still sort under
    # their own parent.
    display_order = _category_display_order(budget)

    # Get budget allocations
    allocations = budget.allocations.select_related("category").all()  # type: ignore[attr-defined]

    comparison: list[dict[str, Any]] = []
    allocated_category_ids: set[int] = set()

    for allocation in allocations:
        category = allocation.category
        if category.pk in excluded_category_ids:
            continue
        budgeted_amount = allocation.amount
        actual_amount = Decimal("0")

        actual_amount = actual_by_category_id.get(category.pk, Decimal("0"))

        difference = budgeted_amount - actual_amount

        comparison.append(
            {
                "category_id": category.pk,
                "category_name": category.name,
                "category_color": category.color,
                "is_subcategory": category.parent_id is not None,
                "budgeted_amount": budgeted_amount,
                "actual_amount": actual_amount,
                "difference": difference,
                "status": _resolve_status(budgeted_amount, actual_amount, difference),
            }
        )
        allocated_category_ids.add(category.pk)

    # Add categories with spending but no allocation
    for row in ordered_rows:
        category_id = row["category_id"]
        if category_id in allocated_category_ids or category_id in excluded_category_ids:
            continue

        actual_amount = actual_by_category_id.get(category_id, Decimal("0"))
        comparison.append(
            {
                "category_id": category_id,
                "category_name": row["category_name"],
                "category_color": row.get("category_color", DEFAULT_CATEGORY_COLOR),
                "is_subcategory": category_id not in top_level_category_ids,
                "budgeted_amount": Decimal("0"),
                "actual_amount": actual_amount,
                "difference": -actual_amount,  # No budget = over by full amount
                "status": "over",
            }
        )

    # Order parents before their own children, keeping unknown ids last by name.
    comparison.sort(
        key=lambda item: (display_order.get(item["category_id"], len(display_order)), item["category_name"])
    )

    return comparison
