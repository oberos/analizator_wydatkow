"""Summary helpers for budget comparison and reporting."""

from decimal import Decimal
from typing import Any

from budgets.models import Budget
from categories.colors import DEFAULT_CATEGORY_COLOR
from transactions.summary import get_user_category_summary


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

    # Build a dict of category_name -> actual data
    actual_by_category = {row["category_name"]: row for row in actual_summary}

    # Get budget allocations
    allocations = budget.allocations.select_related("category").all()  # type: ignore[attr-defined]

    # Build comparison data
    comparison: list[dict[str, Any]] = []
    processed_categories: set[str] = set()

    # Process allocations
    for allocation in allocations:
        category_name = allocation.category.name
        category_color = allocation.category.color
        budgeted_amount = allocation.amount
        actual_amount = Decimal("0")

        # Get actual spending if exists
        if category_name in actual_by_category:
            actual_data = actual_by_category[category_name]
            total_amount = actual_data.get("total_amount")
            if isinstance(total_amount, Decimal):
                actual_amount = total_amount

        # Calculate difference (positive = under budget)
        difference = budgeted_amount - actual_amount

        # Determine status
        if budgeted_amount > 0:
            ratio = abs(difference / budgeted_amount)
            if ratio < Decimal("0.10"):
                status = "close"
            elif difference < 0:
                status = "over"
            else:
                status = "under"
        else:
            # Zero budget: any spending is over
            status = "over" if actual_amount > 0 else "under"

        comparison.append(
            {
                "category_name": category_name,
                "category_color": category_color,
                "budgeted_amount": budgeted_amount,
                "actual_amount": actual_amount,
                "difference": difference,
                "status": status,
            }
        )
        processed_categories.add(category_name)

    # Add categories with spending but no allocation
    for category_name, actual_data in actual_by_category.items():
        if category_name not in processed_categories:
            total_amount = actual_data.get("total_amount")
            actual_amount = total_amount if isinstance(total_amount, Decimal) else Decimal("0")
            comparison.append(
                {
                    "category_name": category_name,
                    "category_color": actual_data.get("category_color", DEFAULT_CATEGORY_COLOR),
                    "budgeted_amount": Decimal("0"),
                    "actual_amount": actual_amount,
                    "difference": -actual_amount,  # No budget = over by full amount
                    "status": "over",
                }
            )

    # Sort by category name
    comparison.sort(key=lambda x: x["category_name"])

    return comparison
