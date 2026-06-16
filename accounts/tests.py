from datetime import date
from decimal import Decimal
from typing import Self
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from transactions.models import Transaction


class DashboardSummaryTests(TestCase):
    def setUp(self: Self) -> None:
        self.user = get_user_model().objects.create_user(username="dashboard-user")
        self.other_user = get_user_model().objects.create_user(username="dashboard-other-user")
        self.client.force_login(self.user)

    def _get_dashboard(self: Self) -> HttpResponse:
        """Request dashboard with a deterministic date range for summary assertions."""
        return self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )

    def _create_transaction(
        self: Self,
        *,
        tx_date: date,
        amount: Decimal,
        transaction_number: str,
        category: Category | None = None,
    ) -> None:
        Transaction.objects.create(
            user=self.user,
            date=tx_date,
            booking_date=tx_date,
            merchant=f"MERCHANT-{transaction_number}",
            description="Dashboard date-range test",
            amount=amount,
            transaction_number=transaction_number,
            category=category,
        )

    def test_dashboard_summary_contains_only_current_user_transactions(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        unknown = Category.objects.get(user=self.user, name="Unknown")
        other_health = Category.objects.get(user=self.other_user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 1),
            booking_date=date(2026, 6, 1),
            merchant="HEALTH SHOP",
            description="Health purchase",
            amount=Decimal("-20.00"),
            transaction_number="DB-1",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 2),
            booking_date=date(2026, 6, 2),
            merchant="UNKNOWN SHOP",
            description="Unknown purchase",
            amount=Decimal("-5.00"),
            transaction_number="DB-2",
            category=unknown,
        )
        Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 6, 3),
            booking_date=date(2026, 6, 3),
            merchant="OTHER USER SHOP",
            description="Other user purchase",
            amount=Decimal("-999.00"),
            transaction_number="DB-3",
            category=other_health,
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row["total_amount"] for row in summary}

        self.assertEqual(by_category["Health"], Decimal("20"))
        self.assertEqual(by_category["Unknown"], Decimal("5"))
        self.assertNotIn("Other User", by_category)
        self.assertNotContains(response, "OTHER USER SHOP")

    def test_dashboard_summary_shows_uncategorized_group(self: Self) -> None:
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 5),
            booking_date=date(2026, 6, 5),
            merchant="NO CATEGORY SHOP",
            description="Unassigned transaction",
            amount=Decimal("-11.00"),
            transaction_number="DB-4",
            category=None,
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row["total_amount"] for row in summary}
        self.assertEqual(by_category["Uncategorized"], Decimal("11"))
        self.assertContains(response, "Uncategorized")

    def test_dashboard_summary_uses_net_category_amount_when_income_exists(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 6),
            booking_date=date(2026, 6, 6),
            merchant="HEALTH EXPENSE",
            description="Health expense",
            amount=Decimal("-50.00"),
            transaction_number="DB-5",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 7),
            booking_date=date(2026, 6, 7),
            merchant="HEALTH REFUND",
            description="Health refund",
            amount=Decimal("15.00"),
            transaction_number="DB-6",
            category=health,
        )

        response = self._get_dashboard()

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row for row in summary}
        self.assertEqual(by_category["Health"]["total_amount"], Decimal("35"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)

    def test_dashboard_uses_default_last_30_days_range_when_query_missing(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 2, 20),
            amount=Decimal("-12.00"),
            transaction_number="DB-DEFAULT-IN",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 1, 10),
            amount=Decimal("-99.00"),
            transaction_number="DB-DEFAULT-OUT",
            category=health,
        )

        with patch("accounts.views._default_dashboard_range", return_value=(date(2026, 2, 1), date(2026, 3, 3))):
            response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        by_category = {row["category_name"]: row["total_amount"] for row in response.context["category_summary"]}
        self.assertEqual(by_category["Health"], Decimal("12"))
        self.assertEqual(response.context["selected_start_date"], date(2026, 2, 1))
        self.assertEqual(response.context["selected_end_date"], date(2026, 3, 3))

    def test_dashboard_invalid_range_shows_error_and_uses_default_summary(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 2, 15),
            amount=Decimal("-33.00"),
            transaction_number="DB-INVALID-DEFAULT",
            category=health,
        )

        with patch("accounts.views._default_dashboard_range", return_value=(date(2026, 2, 1), date(2026, 3, 3))):
            response = self.client.get(
                reverse("dashboard"),
                {"start_date": "2026-03-10", "end_date": "2026-03-01"},
            )

        self.assertEqual(response.status_code, 200)
        by_category = {row["category_name"]: row["total_amount"] for row in response.context["category_summary"]}
        self.assertEqual(by_category["Health"], Decimal("33"))
        self.assertContains(response, "Start date must be on or before end date.")

    def test_dashboard_includes_start_and_end_dates_in_range_filter(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 2, 1),
            amount=Decimal("-10.00"),
            transaction_number="DB-BOUNDARY-START",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 3),
            amount=Decimal("-5.00"),
            transaction_number="DB-BOUNDARY-END",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 1, 31),
            amount=Decimal("-40.00"),
            transaction_number="DB-BOUNDARY-OUT",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-02-01", "end_date": "2026-03-03"},
        )

        self.assertEqual(response.status_code, 200)
        by_category = {row["category_name"]: row for row in response.context["category_summary"]}
        self.assertEqual(by_category["Health"]["total_amount"], Decimal("15"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)

    def test_dashboard_shows_range_empty_state_when_user_has_data_outside_range(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 1, 1),
            amount=Decimal("-25.00"),
            transaction_number="DB-EMPTY-OUTSIDE",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-02-01", "end_date": "2026-02-10"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category_summary"], [])
        self.assertContains(response, "No transactions in selected range.")

    def test_dashboard_query_range_cannot_reveal_other_user_transactions(self: Self) -> None:
        """Verify that changing query params cannot leak other user's summary."""
        health = Category.objects.get(user=self.user, name="Health")
        other_health = Category.objects.get(user=self.other_user, name="Health")

        # Create transaction for current user in 2026-01
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 1, 15),
            booking_date=date(2026, 1, 15),
            merchant="USER HEALTH",
            description="Current user health expense",
            amount=Decimal("-25.00"),
            transaction_number="D1-CUSER",
            category=health,
        )

        # Create transaction for other user in same month
        Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 1, 16),
            booking_date=date(2026, 1, 16),
            merchant="OTHER HEALTH",
            description="Other user health expense",
            amount=Decimal("-50.00"),
            transaction_number="D1-OUSER",
            category=other_health,
        )

        # Query with date range that includes both transactions
        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )

        # Should see only current user's transaction
        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row["total_amount"] for row in summary}
        self.assertEqual(len(by_category), 1)
        self.assertEqual(by_category["Health"], Decimal("25.00"))
