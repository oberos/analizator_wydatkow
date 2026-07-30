"""Tests for budgets app models."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from budgets.models import Budget, BudgetCategoryAllocation
from categories.models import Category

User = get_user_model()


class BudgetModelTests(TestCase):
    """Tests for Budget model validation and behavior."""

    def setUp(self) -> None:  # noqa: ANN101
        """Create test user for budget tests."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")  # noqa: S106

    def test_budget_creation_valid(self) -> None:  # noqa: ANN101
        """Create budget with valid dates — saves successfully."""
        budget = Budget(
            user=self.user,
            name="July 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        budget.save()  # Should not raise
        self.assertEqual(Budget.objects.count(), 1)

    def test_budget_start_after_end_invalid(self) -> None:  # noqa: ANN101
        """Attempt to create budget with start_date > end_date — validation error raised."""
        budget = Budget(
            user=self.user,
            name="Invalid Budget",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 7, 1),
        )
        with self.assertRaises(ValidationError) as cm:
            budget.save()
        self.assertIn("start_date", cm.exception.message_dict)

    def test_budget_overlap_blocked(self) -> None:  # noqa: ANN101
        """Creating overlapping budget for same user — validation error raised."""
        # Create first budget
        Budget.objects.create(
            user=self.user,
            name="July 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        # Attempt to create overlapping budget
        overlapping_budget = Budget(
            user=self.user,
            name="Mid-July 2026",
            start_date=date(2026, 7, 15),
            end_date=date(2026, 8, 15),
        )
        with self.assertRaises(ValidationError) as cm:
            overlapping_budget.save()
        self.assertIn("overlap", str(cm.exception).lower())


class BudgetCategoryAllocationModelTests(TestCase):
    """Tests for BudgetCategoryAllocation model validation and behavior."""

    def setUp(self) -> None:  # noqa: ANN101
        """Create test user, budget, and category."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")  # noqa: S106
        self.budget = Budget.objects.create(
            user=self.user,
            name="July 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        self.category = Category.objects.create(user=self.user, name="Groceries")

    def test_allocation_zero_amount_allowed(self) -> None:  # noqa: ANN101
        """Create BudgetCategoryAllocation with amount=0 — succeeds."""
        allocation = BudgetCategoryAllocation(
            budget=self.budget,
            category=self.category,
            amount=Decimal("0"),
        )
        allocation.save()  # Should not raise
        self.assertEqual(BudgetCategoryAllocation.objects.count(), 1)

    def test_allocation_negative_amount_invalid(self) -> None:  # noqa: ANN101
        """Create BudgetCategoryAllocation with amount=-100 — validation error raised."""
        allocation = BudgetCategoryAllocation(
            budget=self.budget,
            category=self.category,
            amount=Decimal("-100"),
        )
        with self.assertRaises(ValidationError) as cm:
            allocation.save()
        self.assertIn("amount", cm.exception.message_dict)

    def test_category_delete_cascades_allocation(self) -> None:  # noqa: ANN101
        """Delete a category with allocations — allocations cascade delete."""
        # Create allocation
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.category,
            amount=Decimal("1000"),
        )
        self.assertEqual(BudgetCategoryAllocation.objects.count(), 1)

        # Delete category
        self.category.delete()

        # Allocation should be cascade deleted
        self.assertEqual(BudgetCategoryAllocation.objects.count(), 0)
