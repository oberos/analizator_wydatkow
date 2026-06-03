from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from transactions.models import Transaction


class DashboardSummaryTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="dashboard-user")
        self.other_user = get_user_model().objects.create_user(username="dashboard-other-user")
        self.client.force_login(self.user)

    def test_dashboard_summary_contains_only_current_user_transactions(self) -> None:
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

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row["total_amount"] for row in summary}

        self.assertEqual(by_category["Health"], Decimal("20"))
        self.assertEqual(by_category["Unknown"], Decimal("5"))
        self.assertNotIn("Other User", by_category)
        self.assertNotContains(response, "OTHER USER SHOP")

    def test_dashboard_summary_shows_uncategorized_group(self) -> None:
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

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row["total_amount"] for row in summary}
        self.assertEqual(by_category["Uncategorized"], Decimal("11"))
        self.assertContains(response, "Uncategorized")

    def test_dashboard_summary_uses_net_category_amount_when_income_exists(self) -> None:
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

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        summary = response.context["category_summary"]
        by_category = {row["category_name"]: row for row in summary}
        self.assertEqual(by_category["Health"]["total_amount"], Decimal("35"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)
