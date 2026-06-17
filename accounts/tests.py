from datetime import date
from decimal import Decimal
from typing import Self
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from categories.models import Category
from transactions.models import Transaction


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.core.files.storage.FileSystemStorage"}})
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

    def test_dashboard_summary_contains_only_current_user_transactions(
        self: Self,
    ) -> None:
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

    def test_dashboard_summary_uses_net_category_amount_when_income_exists(
        self: Self,
    ) -> None:
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

    def test_dashboard_uses_default_last_30_days_range_when_query_missing(
        self: Self,
    ) -> None:
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

        with patch(
            "accounts.views._default_dashboard_range",
            return_value=(date(2026, 2, 1), date(2026, 3, 3)),
        ):
            response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        by_category = {row["category_name"]: row["total_amount"] for row in response.context["category_summary"]}
        self.assertEqual(by_category["Health"], Decimal("12"))
        self.assertEqual(response.context["selected_start_date"], date(2026, 2, 1))
        self.assertEqual(response.context["selected_end_date"], date(2026, 3, 3))

    def test_dashboard_invalid_range_shows_error_and_uses_default_summary(
        self: Self,
    ) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 2, 15),
            amount=Decimal("-33.00"),
            transaction_number="DB-INVALID-DEFAULT",
            category=health,
        )

        with patch(
            "accounts.views._default_dashboard_range",
            return_value=(date(2026, 2, 1), date(2026, 3, 3)),
        ):
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

    def test_dashboard_shows_range_empty_state_when_user_has_data_outside_range(
        self: Self,
    ) -> None:
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

    def test_dashboard_exposes_chart_payload_from_summary_rows(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        unknown = Category.objects.get(user=self.user, name="Unknown")
        savings = Category.objects.get(user=self.user, name="Savings")

        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("-20.00"),
            transaction_number="DB-CHART-HEALTH",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 3),
            amount=Decimal("-5.00"),
            transaction_number="DB-CHART-UNKNOWN",
            category=unknown,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 4),
            amount=Decimal("-3.50"),
            transaction_number="DB-CHART-UNCATEGORIZED",
            category=None,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 5),
            amount=Decimal("15.00"),
            transaction_number="DB-CHART-SAVINGS-INCOME",
            category=savings,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["chart_labels"], ["Health", "Uncategorized", "Unknown"])
        self.assertEqual(response.context["chart_values"], [20.0, 3.5, 5.0])
        self.assertEqual(response.context["chart_excluded_non_positive_categories"], ["Savings"])
        self.assertTrue(response.context["chart_is_renderable"])

    def test_dashboard_chart_payload_is_not_renderable_without_positive_totals(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("10.00"),
            transaction_number="DB-CHART-INCOME-ONLY",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["chart_labels"], [])
        self.assertEqual(response.context["chart_values"], [])
        self.assertEqual(response.context["chart_excluded_non_positive_categories"], ["Health"])
        self.assertFalse(response.context["chart_is_renderable"])

    def test_dashboard_renders_chart_block_when_payload_is_renderable(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("-20.00"),
            transaction_number="DB-CHART-RENDERABLE",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertContains(response, 'id="dashboard-pie-chart-section"', html=False)
        self.assertContains(response, 'id="dashboard-category-pie-chart"', html=False)
        self.assertContains(response, 'id="dashboard-chart-labels"', html=False)
        self.assertContains(response, 'id="dashboard-chart-values"', html=False)

    def test_dashboard_does_not_render_chart_block_for_empty_selected_range(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 1, 1),
            amount=Decimal("-25.00"),
            transaction_number="DB-CHART-EMPTY-RANGE",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-02-01", "end_date": "2026-02-10"},
        )

        self.assertNotContains(response, 'id="dashboard-pie-chart-section"', html=False)
        self.assertContains(response, "No transactions in selected range.")

    def test_dashboard_renders_non_positive_exclusion_note_when_relevant(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        savings = Category.objects.get(user=self.user, name="Savings")
        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("-20.00"),
            transaction_number="DB-CHART-NOTE-POSITIVE",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 3),
            amount=Decimal("10.00"),
            transaction_number="DB-CHART-NOTE-NONPOSITIVE",
            category=savings,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertContains(response, 'id="dashboard-chart-positive-note"', html=False)
        self.assertContains(response, "Pie chart visualizes positive spending only.")
        self.assertContains(response, "Savings")

    def test_dashboard_chart_values_match_positive_summary_totals(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        unknown = Category.objects.get(user=self.user, name="Unknown")
        savings = Category.objects.get(user=self.user, name="Savings")

        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("-20.00"),
            transaction_number="DB-CHART-PARITY-HEALTH",
            category=health,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 3),
            amount=Decimal("-5.00"),
            transaction_number="DB-CHART-PARITY-UNKNOWN",
            category=unknown,
        )
        self._create_transaction(
            tx_date=date(2026, 3, 4),
            amount=Decimal("10.00"),
            transaction_number="DB-CHART-PARITY-SAVINGS",
            category=savings,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        positive_summary: dict[str, float] = {}
        for row in response.context["category_summary"]:
            category_name = row["category_name"]
            total_amount = row["total_amount"]
            if isinstance(category_name, str) and isinstance(total_amount, Decimal) and total_amount > 0:
                positive_summary[category_name] = float(total_amount)
        chart_series = dict(zip(response.context["chart_labels"], response.context["chart_values"], strict=True))
        self.assertEqual(chart_series, positive_summary)

    def test_dashboard_keeps_unavailable_fallback_container_for_chart_runtime_failures(self: Self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        self._create_transaction(
            tx_date=date(2026, 3, 2),
            amount=Decimal("-20.00"),
            transaction_number="DB-CHART-FALLBACK",
            category=health,
        )

        response = self.client.get(
            reverse("dashboard"),
            {"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="dashboard-chart-unavailable"', html=False)
        self.assertContains(response, "Chart unavailable. Summary table remains the source of truth.")
