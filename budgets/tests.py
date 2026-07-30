"""Tests for budgets app models."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from budgets.forms import BudgetForm
from budgets.models import Budget, BudgetCategoryAllocation
from budgets.summary import get_budget_comparison
from categories.models import Category
from transactions.models import Transaction

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


class BudgetFormTests(TestCase):
    """Tests for BudgetForm validation."""

    def setUp(self) -> None:  # noqa: ANN101
        """Create test user."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")  # noqa: S106

    def test_form_valid_dates(self) -> None:  # noqa: ANN101
        """Form with valid dates passes validation."""
        form = BudgetForm(
            data={
                "name": "July 2026",
                "start_date": "01/07/2026",
                "end_date": "31/07/2026",
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_form_start_after_end_invalid(self) -> None:  # noqa: ANN101
        """Form validation catches start_date > end_date."""
        form = BudgetForm(
            data={
                "name": "Invalid Budget",
                "start_date": "31/07/2026",
                "end_date": "01/07/2026",
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Start date must be on or before end date", str(form.errors))

    def test_form_overlap_validation(self) -> None:  # noqa: ANN101
        """Form validation catches overlapping dates with clear error message."""
        # Create existing budget
        Budget.objects.create(
            user=self.user,
            name="July 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        # Attempt to create overlapping budget
        form = BudgetForm(
            data={
                "name": "Mid-July 2026",
                "start_date": "15/07/2026",
                "end_date": "15/08/2026",
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("overlap", str(form.errors).lower())


class BudgetComparisonTests(TestCase):
    """Tests for get_budget_comparison helper function."""

    def setUp(self) -> None:  # noqa: ANN101
        """Create test user, budget, and categories."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")  # noqa: S106
        self.budget = Budget.objects.create(
            user=self.user,
            name="July 2026",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
        )
        self.groceries = Category.objects.create(user=self.user, name="Groceries")
        self.transport = Category.objects.create(user=self.user, name="Transport")

    def test_comparison_under_budget(self) -> None:  # noqa: ANN101
        """budgeted=1000, actual=800 → difference=200, status='under'."""
        # Create allocation
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.groceries,
            amount=Decimal("1000"),
        )
        # Create transactions (negative = expense)
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 7, 15),
            merchant="Store",
            description="Groceries",
            amount=Decimal("-800"),
            category=self.groceries,
        )

        comparison = get_budget_comparison(self.budget)

        self.assertEqual(len(comparison), 1)
        row = comparison[0]
        self.assertEqual(row["category_name"], "Groceries")
        self.assertEqual(row["budgeted_amount"], Decimal("1000"))
        self.assertEqual(row["actual_amount"], Decimal("800"))
        self.assertEqual(row["difference"], Decimal("200"))
        self.assertEqual(row["status"], "under")

    def test_comparison_over_budget(self) -> None:  # noqa: ANN101
        """budgeted=500, actual=600 → difference=-100, status='over'."""
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.transport,
            amount=Decimal("500"),
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 7, 15),
            merchant="Gas Station",
            description="Fuel",
            amount=Decimal("-600"),
            category=self.transport,
        )

        comparison = get_budget_comparison(self.budget)

        row = comparison[0]
        self.assertEqual(row["difference"], Decimal("-100"))
        self.assertEqual(row["status"], "over")

    def test_comparison_close_to_budget(self) -> None:  # noqa: ANN101
        """budgeted=1000, actual=950 → status='close'."""
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.groceries,
            amount=Decimal("1000"),
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 7, 15),
            merchant="Store",
            description="Groceries",
            amount=Decimal("-950"),
            category=self.groceries,
        )

        comparison = get_budget_comparison(self.budget)

        row = comparison[0]
        self.assertEqual(row["status"], "close")

    def test_comparison_zero_budget(self) -> None:  # noqa: ANN101
        """budgeted=0, actual=100 → status='over'."""
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.groceries,
            amount=Decimal("0"),
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 7, 15),
            merchant="Store",
            description="Groceries",
            amount=Decimal("-100"),
            category=self.groceries,
        )

        comparison = get_budget_comparison(self.budget)

        row = comparison[0]
        self.assertEqual(row["budgeted_amount"], Decimal("0"))
        self.assertEqual(row["actual_amount"], Decimal("100"))
        self.assertEqual(row["status"], "over")

    def test_comparison_no_allocation_but_spending(self) -> None:  # noqa: ANN101
        """Category not in budget but has transactions → appears in comparison as 'over'."""
        # No allocation for transport
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 7, 15),
            merchant="Gas Station",
            description="Fuel",
            amount=Decimal("-200"),
            category=self.transport,
        )

        comparison = get_budget_comparison(self.budget)

        self.assertEqual(len(comparison), 1)
        row = comparison[0]
        self.assertEqual(row["category_name"], "Transport")
        self.assertEqual(row["budgeted_amount"], Decimal("0"))
        self.assertEqual(row["actual_amount"], Decimal("200"))
        self.assertEqual(row["status"], "over")

    def test_comparison_allocation_no_spending(self) -> None:  # noqa: ANN101
        """budgeted=500, actual=0 → difference=500, status='under'."""
        BudgetCategoryAllocation.objects.create(
            budget=self.budget,
            category=self.groceries,
            amount=Decimal("500"),
        )
        # No transactions

        comparison = get_budget_comparison(self.budget)

        row = comparison[0]
        self.assertEqual(row["budgeted_amount"], Decimal("500"))
        self.assertEqual(row["actual_amount"], Decimal("0"))
        self.assertEqual(row["difference"], Decimal("500"))
        self.assertEqual(row["status"], "under")
