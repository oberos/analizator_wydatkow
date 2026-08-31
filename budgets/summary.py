"""Summary helpers for budget comparison and reporting."""

from decimal import Decimal
from typing import Any

from budgets.models import Budget
from categories.colors import DEFAULT_CATEGORY_COLOR
from transactions.summary import flatten_category_summary, get_user_category_summary


def _resolve_status(budgeted_amount: Decimal, actual_amount: Decimal, difference: Decimal) -> str:
    """Classify an allocation as under, over, or close to its budget."""
    if budgeted_amount > 0:
        ratio = abs(difference / budgeted_amount)
        if ratio < Decimal("0.10"):
            return "close"
        return "over" if difference < 0 else "under"
    # Zero budget: any spending is over
    return "over" if actual_amount > 0 else "under"


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

    # Key by category id: names are only unique per parent, so a name-keyed lookup
    # would collide between subcategories sharing a name under different parents.
    ordered_rows = flatten_category_summary(actual_summary)
    actual_by_category_id = {row["category_id"]: row for row in ordered_rows}
    top_level_category_ids = {row["category_id"] for row in actual_summary}
    # Preserves the parent-then-children order for the final sort.
    display_order = {row["category_id"]: index for index, row in enumerate(ordered_rows)}

    # Get budget allocations
    allocations = budget.allocations.select_related("category").all()  # type: ignore[attr-defined]

    comparison: list[dict[str, Any]] = []
    allocated_category_ids: set[int] = set()

    for allocation in allocations:
        category = allocation.category
        budgeted_amount = allocation.amount
        actual_amount = Decimal("0")

        actual_data = actual_by_category_id.get(category.pk)
        if actual_data is not None:
            total_amount = actual_data.get("total_amount")
            if isinstance(total_amount, Decimal):
                actual_amount = total_amount

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
        if category_id in allocated_category_ids:
            continue

        total_amount = row.get("total_amount")
        actual_amount = total_amount if isinstance(total_amount, Decimal) else Decimal("0")
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
