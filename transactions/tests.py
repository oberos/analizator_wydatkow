# ruff: noqa: ANN101
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES

from .categorization import categorize_transaction, normalize_merchant
from .mappings import PREDEFINED_CATEGORY_GROUPS, PREDEFINED_MAPPINGS
from .models import MerchantCategoryMapping, Transaction
from .refinement import apply_category_correction
from .summary import get_user_category_summary


class PredefinedMappingSeedTests(TestCase):
    def test_predefined_mapping_category_groups_align_with_runtime_taxonomy(self) -> None:
        expected_categories = set(PREDEFINED_CATEGORIES) - {"Unknown"}
        self.assertEqual(set(PREDEFINED_CATEGORY_GROUPS), expected_categories)

    def test_new_user_gets_predefined_mappings_without_missing_categories(self) -> None:
        user = get_user_model().objects.create_user(username="mapping-seed-user")
        user_category_names = set(Category.objects.filter(user=user).values_list("name", flat=True))
        user_mappings = MerchantCategoryMapping.objects.filter(user=user).select_related("category")

        self.assertEqual(user_mappings.count(), len(PREDEFINED_MAPPINGS))
        self.assertTrue(user_mappings.exists())

        for mapping in user_mappings:
            self.assertIn(mapping.category.name, user_category_names)


class CategorizationTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="categorization-user")

    def test_categorize_transaction_matches_representative_merchants(self) -> None:
        test_cases = [
            ("REVOLUT", "Finance"),
            ("NETFLIX", "Bills"),
            (' FHU "AGA"-LEWIATAN 2  Ruda Slaska ', "Food and Household Chemicals"),
            ("ORLEN STACJA NR 100 MIKOLOW - BOR", "Transportation"),
            ("PPK", "Savings"),
            ("APTEKA HYGIEIA SWIETOCHLOWIC POL", "Health"),
            ("ROSSMANN SKLEP 1337 SWIETOCHLOWIC", "Beauty"),
            ("PEPCO", "Clothing and Footwear"),
            ("DECATHLON", "Sports"),
            ("MCDONALDS", "Restaurants"),
            ("MULTIKINO", "Recreation"),
            ("IKEA", "Home"),
            ("Unknown Merchant", None),
            ("SHOPPINGBPARK", None),
        ]

        for raw_merchant, expected_category_name in test_cases:
            category = categorize_transaction(self.user, raw_merchant)
            category_name = category.name if category else None
            self.assertEqual(category_name, expected_category_name)

    def test_categorize_transaction_handles_known_punctuation_variants(self) -> None:
        test_cases = [
            (' FHU "AGA"-LEWIATAN 2  Ruda Slaska ', "Food and Household Chemicals"),
            ("APTEKA/24 ZIKO SWIETOCHLOWICE POL", "Health"),
            ("CINEMA CITY - KATOWICE", "Recreation"),
        ]

        for raw_merchant, expected_category_name in test_cases:
            category = categorize_transaction(self.user, raw_merchant)
            category_name = category.name if category else None
            self.assertEqual(category_name, expected_category_name)

    def test_categorize_transaction_avoids_false_positives_for_short_keys(self) -> None:
        test_cases = [
            ("SHOPPINGBPARK", None),
            ("BIKESTORE", None),
            ("BOOKINGCOM", None),
        ]

        for raw_merchant, expected_category_name in test_cases:
            category = categorize_transaction(self.user, raw_merchant)
            category_name = category.name if category else None
            self.assertEqual(category_name, expected_category_name)

    def test_categorize_transaction_uses_same_matching_with_cache(self) -> None:
        mappings = MerchantCategoryMapping.objects.filter(user=self.user).select_related("category")
        mappings_cache = {mapping.normalized_merchant: mapping.category for mapping in mappings}

        category = categorize_transaction(
            self.user,
            "CIRCLE K RUDA SLAS RUDA SLLSKA 417",
            mappings_cache,
        )

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "Transportation")  # type: ignore[union-attr]


class ImportFlowAndRolloutTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="import-user")
        self.client.force_login(self.user)

    def _build_ing_csv(self) -> bytes:
        rows = [
            "Data transakcji;Data księgowania;Dane kontrahenta;Tytuł;Kwota transakcji (waluta rachunku);Nr transakcji",
            "2026-05-01;2026-05-01;BIEDRONKA;Zakupy spozywcze;-120,50;TX-1",
            "2026-05-02;2026-05-02;UNMAPPED MERCHANT;Zakup testowy;-15,99;TX-2",
        ]
        return "\n".join(rows).encode("windows-1250")

    def _build_ing_csv_with_rows(self, rows: list[str]) -> bytes:
        header = (
            "Data transakcji;Data księgowania;Dane kontrahenta;Tytuł;Kwota transakcji (waluta rachunku);Nr transakcji"
        )
        return "\n".join([header, *rows]).encode("windows-1250")

    def test_upload_flow_categorizes_and_skips_duplicates(self) -> None:
        upload = SimpleUploadedFile("ing.csv", self._build_ing_csv(), content_type="text/csv")
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        imported = Transaction.objects.filter(user=self.user).order_by("transaction_number")
        self.assertEqual(imported.count(), 2)

        category_by_tx_number = {tx.transaction_number: tx.category.name for tx in imported}  # type: ignore[union-attr]
        self.assertEqual(category_by_tx_number["TX-1"], "Food and Household Chemicals")
        self.assertEqual(category_by_tx_number["TX-2"], "Unknown")

        second_upload = SimpleUploadedFile("ing.csv", self._build_ing_csv(), content_type="text/csv")
        self.client.post(reverse("transactions:upload"), {"csv_file": second_upload})
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 2)

    def test_upload_with_malformed_amount_aborts_without_partial_persistence(self) -> None:
        invalid_csv = self._build_ing_csv_with_rows(
            [
                "2026-05-01;2026-05-01;BIEDRONKA;Zakupy spozywcze;-120,50;TX-M-1",
                "2026-05-02;2026-05-02;BROKEN MERCHANT;Zakup testowy;INVALID;TX-M-2",
            ]
        )
        upload = SimpleUploadedFile("malformed.csv", invalid_csv, content_type="text/csv")

        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSV parsing error:")
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)

    def test_upload_mixed_duplicate_and_new_rows_reports_correct_counts(self) -> None:
        existing_unknown = Category.objects.get(user=self.user, name="Unknown")
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 5, 1),
            booking_date=date(2026, 5, 1),
            merchant="BIEDRONKA",
            description="Zakupy spozywcze",
            amount="-120.50",
            transaction_number="TX-D-1",
            category=existing_unknown,
        )

        mixed_csv = self._build_ing_csv_with_rows(
            [
                "2026-05-01;2026-05-01;BIEDRONKA;Zakupy spozywcze;-120,50;TX-D-1",
                "2026-05-03;2026-05-03;UNMAPPED MERCHANT;Nowy zakup;-9,99;TX-D-2",
            ]
        )
        upload = SimpleUploadedFile("mixed.csv", mixed_csv, content_type="text/csv")

        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Imported 1 transactions, skipped 1 duplicates.")
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 2)
        self.assertTrue(Transaction.objects.filter(user=self.user, transaction_number="TX-D-2").exists())

    def test_delete_all_flow_removes_only_current_user_transactions(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        other_user = get_user_model().objects.create_user(username="other-import-user")
        other_unknown_category = Category.objects.get(user=other_user, name="Unknown")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 5, 1),
            booking_date=date(2026, 5, 1),
            merchant="BIEDRONKA",
            description="Zakupy",
            amount="-10.00",
            transaction_number="SELF-1",
            category=unknown_category,
        )
        Transaction.objects.create(
            user=other_user,
            date=date(2026, 5, 1),
            booking_date=date(2026, 5, 1),
            merchant="BIEDRONKA",
            description="Zakupy",
            amount="-20.00",
            transaction_number="OTHER-1",
            category=other_unknown_category,
        )

        response = self.client.post(reverse("transactions:delete_all"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Transaction.objects.filter(user=other_user).count(), 1)

    def test_existing_user_update_does_not_backfill_categories_or_mappings(self) -> None:
        initial_category_count = Category.objects.filter(user=self.user).count()
        initial_mapping_count = MerchantCategoryMapping.objects.filter(user=self.user).count()

        self.user.first_name = "Updated"
        self.user.save()

        self.assertEqual(Category.objects.filter(user=self.user).count(), initial_category_count)
        self.assertEqual(MerchantCategoryMapping.objects.filter(user=self.user).count(), initial_mapping_count)


class TransactionCategoryCorrectionTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="refinement-user")
        self.other_user = get_user_model().objects.create_user(username="refinement-other-user")
        self.client.force_login(self.user)

    def _create_transaction(self, transaction_number: str, merchant: str, category: Category) -> Transaction:
        return Transaction.objects.create(
            user=self.user,
            date=date(2026, 5, 1),
            booking_date=date(2026, 5, 1),
            merchant=merchant,
            description="Refinement test",
            amount="-30.00",
            transaction_number=transaction_number,
            category=category,
        )

    def _build_ing_csv(self, *, merchant: str, transaction_number: str) -> bytes:
        rows = [
            "Data transakcji;Data księgowania;Dane kontrahenta;Tytuł;Kwota transakcji (waluta rachunku);Nr transakcji",
            f"2026-05-20;2026-05-20;{merchant};Zakup testowy;-21,37;{transaction_number}",
        ]
        return "\n".join(rows).encode("windows-1250")

    def test_transaction_list_renders_category_selectors_with_user_scoped_options(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        tx = self._create_transaction("REF-LIST-1", "LIST MERCHANT", unknown_category)
        own_extra_category = Category.objects.create(user=self.user, name="Own Extra Category")
        Category.objects.create(user=self.other_user, name="Foreign Only Category")

        response = self.client.get(reverse("transactions:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("transactions:set_category", kwargs={"pk": tx.pk})}"')
        self.assertContains(response, 'name="category"', html=False)
        self.assertContains(response, own_extra_category.name)
        self.assertNotContains(response, "Foreign Only Category")

    def test_transaction_list_hides_other_users_transactions(self) -> None:
        own_unknown = Category.objects.get(user=self.user, name="Unknown")
        other_unknown = Category.objects.get(user=self.other_user, name="Unknown")

        self._create_transaction("REF-LIST-SELF", "OWN VISIBLE MERCHANT", own_unknown)
        Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 5, 2),
            booking_date=date(2026, 5, 2),
            merchant="FOREIGN HIDDEN MERCHANT",
            description="Foreign transaction",
            amount="-18.00",
            transaction_number="REF-LIST-FOREIGN",
            category=other_unknown,
        )

        response = self.client.get(reverse("transactions:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OWN VISIBLE MERCHANT")
        self.assertNotContains(response, "FOREIGN HIDDEN MERCHANT")
        rendered_ids = {tx.pk for tx in response.context["transactions"]}
        self.assertNotIn(
            Transaction.objects.get(user=self.other_user, transaction_number="REF-LIST-FOREIGN").pk, rendered_ids
        )

    def test_set_category_updates_transaction_and_creates_mapping(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        target_category = Category.objects.get(user=self.user, name="Health")
        tx = self._create_transaction("REF-1", "TEST MERCHANT", unknown_category)

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(target_category.pk)},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        tx.refresh_from_db()

        self.assertEqual(tx.category, target_category)

        mapping = MerchantCategoryMapping.objects.get(
            user=self.user,
            normalized_merchant=normalize_merchant("TEST MERCHANT"),
        )
        self.assertEqual(mapping.category, target_category)

    def test_set_category_to_unknown_removes_mapping(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        source_category = Category.objects.get(user=self.user, name="Health")
        tx = self._create_transaction("REF-2", "UNKNOWN RESET MERCHANT", source_category)
        normalized_merchant = normalize_merchant(str(tx.merchant))
        MerchantCategoryMapping.objects.create(
            user=self.user,
            normalized_merchant=normalized_merchant,
            category=source_category,
        )

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(unknown_category.pk)},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        tx.refresh_from_db()
        self.assertEqual(tx.category, unknown_category)
        self.assertFalse(
            MerchantCategoryMapping.objects.filter(
                user=self.user,
                normalized_merchant=normalized_merchant,
            ).exists()
        )

    def test_clear_category_removes_mapping_and_sets_null_category(self) -> None:
        source_category = Category.objects.get(user=self.user, name="Health")
        tx = self._create_transaction("REF-3", "CLEAR CATEGORY MERCHANT", source_category)
        normalized_merchant = normalize_merchant(str(tx.merchant))
        MerchantCategoryMapping.objects.create(
            user=self.user,
            normalized_merchant=normalized_merchant,
            category=source_category,
        )

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": ""},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        tx.refresh_from_db()

        self.assertIsNone(tx.category)
        self.assertFalse(
            MerchantCategoryMapping.objects.filter(
                user=self.user,
                normalized_merchant=normalized_merchant,
            ).exists()
        )

    def test_rejects_category_owned_by_other_user(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        tx = self._create_transaction("REF-4", "FOREIGN CATEGORY MERCHANT", unknown_category)
        foreign_category = Category.objects.get(user=self.other_user, name="Health")

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(foreign_category.pk)},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        tx.refresh_from_db()
        self.assertEqual(tx.category, unknown_category)
        self.assertFalse(
            MerchantCategoryMapping.objects.filter(
                user=self.user,
                normalized_merchant=normalize_merchant(str(tx.merchant)),
            ).exists()
        )

    def test_rejects_updates_for_transaction_owned_by_other_user(self) -> None:
        own_health_category = Category.objects.get(user=self.user, name="Health")
        other_unknown_category = Category.objects.get(user=self.other_user, name="Unknown")
        other_tx = Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 5, 1),
            booking_date=date(2026, 5, 1),
            merchant="OTHER USER MERCHANT",
            description="Other user's transaction",
            amount="-45.00",
            transaction_number="REF-5",
            category=other_unknown_category,
        )

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": other_tx.pk}),
            {"category": str(own_health_category.pk)},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))  # type: ignore[attr-defined]

        other_tx.refresh_from_db()
        self.assertEqual(other_tx.category, other_unknown_category)

    def test_category_correction_learning_applies_on_future_import(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        health_category = Category.objects.get(user=self.user, name="Health")
        merchant = "LEARNED MERCHANT"
        tx = self._create_transaction("REF-LEARN-1", merchant, unknown_category)

        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(health_category.pk)},
        )

        upload = SimpleUploadedFile(
            "learn.csv",
            self._build_ing_csv(merchant=merchant, transaction_number="REF-LEARN-2"),
            content_type="text/csv",
        )
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        imported_tx = Transaction.objects.get(user=self.user, transaction_number="REF-LEARN-2")
        self.assertEqual(imported_tx.category, health_category)

    def test_category_correction_learning_applies_to_normalized_merchant_variants(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        health_category = Category.objects.get(user=self.user, name="Health")
        corrected_merchant = "JMP S.A. LEWIATAN 4936 SWIETOCHLOWICE POL"
        future_import_merchant = "LEWIATAN"
        tx = self._create_transaction("REF-VAR-1", corrected_merchant, unknown_category)

        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(health_category.pk)},
        )

        learned_mapping = MerchantCategoryMapping.objects.get(
            user=self.user,
            normalized_merchant=normalize_merchant(corrected_merchant),
        )
        self.assertEqual(learned_mapping.category, health_category)

        upload = SimpleUploadedFile(
            "variant.csv",
            self._build_ing_csv(merchant=future_import_merchant, transaction_number="REF-VAR-2"),
            content_type="text/csv",
        )
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        imported_tx = Transaction.objects.get(user=self.user, transaction_number="REF-VAR-2")
        self.assertEqual(imported_tx.category, health_category)

    def test_category_correction_learning_applies_to_punctuation_variant(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        health_category = Category.objects.get(user=self.user, name="Health")
        corrected_merchant = "APTEKA/24 ZIKO SWIETOCHLOWICE POL"
        future_import_merchant = "ZIKO"
        tx = self._create_transaction("REF-PUNC-1", corrected_merchant, unknown_category)

        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(health_category.pk)},
        )

        upload = SimpleUploadedFile(
            "punctuation.csv",
            self._build_ing_csv(merchant=future_import_merchant, transaction_number="REF-PUNC-2"),
            content_type="text/csv",
        )
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        imported_tx = Transaction.objects.get(user=self.user, transaction_number="REF-PUNC-2")
        self.assertEqual(imported_tx.category, health_category)

    def test_unknown_reset_prevents_future_auto_category(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        health_category = Category.objects.get(user=self.user, name="Health")
        merchant = "RESET MERCHANT"
        tx = self._create_transaction("REF-RESET-1", merchant, unknown_category)

        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(health_category.pk)},
        )
        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(unknown_category.pk)},
        )

        upload = SimpleUploadedFile(
            "reset.csv",
            self._build_ing_csv(merchant=merchant, transaction_number="REF-RESET-2"),
            content_type="text/csv",
        )
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        imported_tx = Transaction.objects.get(user=self.user, transaction_number="REF-RESET-2")
        self.assertEqual(imported_tx.category, unknown_category)

    def test_overlapping_learned_mapping_prefers_more_specific_merchant_key(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        broad_category = Category.objects.get(user=self.user, name="Health")
        specific_category = Category.objects.get(user=self.user, name="Restaurants")

        broad_tx = self._create_transaction("REF-OVERLAP-1", "BIEDRONKA", unknown_category)
        specific_tx = self._create_transaction("REF-OVERLAP-2", "BIEDRONKA MARKET", unknown_category)

        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": broad_tx.pk}),
            {"category": str(broad_category.pk)},
        )
        self.client.post(
            reverse("transactions:set_category", kwargs={"pk": specific_tx.pk}),
            {"category": str(specific_category.pk)},
        )

        upload = SimpleUploadedFile(
            "overlap.csv",
            self._build_ing_csv(
                merchant="BIEDRONKA MARKET KATOWICE",
                transaction_number="REF-OVERLAP-3",
            ),
            content_type="text/csv",
        )
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        imported_tx = Transaction.objects.get(user=self.user, transaction_number="REF-OVERLAP-3")
        self.assertEqual(imported_tx.category, specific_category)


class TransactionSummaryTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="summary-user")
        self.other_user = get_user_model().objects.create_user(username="summary-other-user")

    def test_summary_groups_unknown_and_uncategorized(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        unknown = Category.objects.get(user=self.user, name="Unknown")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 10),
            booking_date=date(2026, 6, 10),
            merchant="HEALTH MERCHANT",
            description="Health payment",
            amount="-15.00",
            transaction_number="SUM-1",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 11),
            booking_date=date(2026, 6, 11),
            merchant="UNKNOWN MERCHANT",
            description="Unknown payment",
            amount="-8.00",
            transaction_number="SUM-2",
            category=unknown,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 12),
            booking_date=date(2026, 6, 12),
            merchant="NO CATEGORY MERCHANT",
            description="No category payment",
            amount="-3.50",
            transaction_number="SUM-3",
            category=None,
        )

        summary = get_user_category_summary(self.user)
        by_category = {row["category_name"]: row["total_amount"] for row in summary}

        self.assertEqual(by_category["Health"], Decimal("15.00"))
        self.assertEqual(by_category["Unknown"], Decimal("8.00"))
        self.assertEqual(by_category["Uncategorized"], Decimal("3.50"))

    def test_summary_is_scoped_to_user(self) -> None:
        self_health = Category.objects.get(user=self.user, name="Health")
        other_health = Category.objects.get(user=self.other_user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 13),
            booking_date=date(2026, 6, 13),
            merchant="SELF MERCHANT",
            description="Self payment",
            amount="-5.00",
            transaction_number="SUM-4",
            category=self_health,
        )
        Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 6, 14),
            booking_date=date(2026, 6, 14),
            merchant="OTHER MERCHANT",
            description="Other payment",
            amount="-200.00",
            transaction_number="SUM-5",
            category=other_health,
        )

        summary = get_user_category_summary(self.user)
        by_category = {row["category_name"]: row["total_amount"] for row in summary}

        self.assertEqual(by_category["Health"], Decimal("5.00"))

    def test_summary_counts_net_spend_with_income_offset_per_category(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 15),
            booking_date=date(2026, 6, 15),
            merchant="HEALTH SPEND",
            description="Expense",
            amount="-40.00",
            transaction_number="SUM-6",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 16),
            booking_date=date(2026, 6, 16),
            merchant="HEALTH REFUND",
            description="Refund",
            amount="10.00",
            transaction_number="SUM-7",
            category=health,
        )

        summary = get_user_category_summary(self.user)
        by_category = {row["category_name"]: row for row in summary}

        self.assertEqual(by_category["Health"]["total_amount"], Decimal("30.00"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)

    def test_summary_returns_negative_total_for_income_only_category(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 17),
            booking_date=date(2026, 6, 17),
            merchant="HEALTH REIMBURSEMENT",
            description="Income only",
            amount="10.00",
            transaction_number="SUM-8",
            category=health,
        )

        summary = get_user_category_summary(self.user)
        by_category = {row["category_name"]: row for row in summary}

        self.assertEqual(by_category["Health"]["total_amount"], Decimal("-10.00"))
        self.assertEqual(by_category["Health"]["transaction_count"], 1)

    def test_summary_can_return_zero_total_when_expense_equals_income(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 18),
            booking_date=date(2026, 6, 18),
            merchant="HEALTH EXPENSE EQUAL",
            description="Expense",
            amount="-10.00",
            transaction_number="SUM-9",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 19),
            booking_date=date(2026, 6, 19),
            merchant="HEALTH INCOME EQUAL",
            description="Income",
            amount="10.00",
            transaction_number="SUM-10",
            category=health,
        )

        summary = get_user_category_summary(self.user)
        by_category = {row["category_name"]: row for row in summary}

        self.assertEqual(by_category["Health"]["total_amount"], Decimal("0.00"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)

    def test_summary_filters_by_inclusive_date_range(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 1),
            booking_date=date(2026, 6, 1),
            merchant="RANGE START",
            description="Range start",
            amount="-10.00",
            transaction_number="SUM-RANGE-1",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 10),
            booking_date=date(2026, 6, 10),
            merchant="RANGE END",
            description="Range end",
            amount="-5.00",
            transaction_number="SUM-RANGE-2",
            category=health,
        )
        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 11),
            booking_date=date(2026, 6, 11),
            merchant="RANGE OUTSIDE",
            description="Range outside",
            amount="-99.00",
            transaction_number="SUM-RANGE-3",
            category=health,
        )

        summary = get_user_category_summary(self.user, start_date=date(2026, 6, 1), end_date=date(2026, 6, 10))
        by_category = {row["category_name"]: row for row in summary}

        self.assertEqual(by_category["Health"]["total_amount"], Decimal("15.00"))
        self.assertEqual(by_category["Health"]["transaction_count"], 2)

    def test_summary_date_range_filter_keeps_user_scope(self) -> None:
        health = Category.objects.get(user=self.user, name="Health")
        other_health = Category.objects.get(user=self.other_user, name="Health")

        Transaction.objects.create(
            user=self.user,
            date=date(2026, 6, 2),
            booking_date=date(2026, 6, 2),
            merchant="OWN RANGE TX",
            description="Own range tx",
            amount="-20.00",
            transaction_number="SUM-RANGE-OWN",
            category=health,
        )
        Transaction.objects.create(
            user=self.other_user,
            date=date(2026, 6, 2),
            booking_date=date(2026, 6, 2),
            merchant="FOREIGN RANGE TX",
            description="Foreign range tx",
            amount="-500.00",
            transaction_number="SUM-RANGE-FOREIGN",
            category=other_health,
        )

        summary = get_user_category_summary(self.user, start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        by_category = {row["category_name"]: row["total_amount"] for row in summary}

        self.assertEqual(by_category["Health"], Decimal("20.00"))


class TransactionRefinementServiceSafetyTests(TestCase):
    def test_rejects_transaction_owned_by_another_user(self) -> None:
        user = get_user_model().objects.create_user(username="service-safe-user")
        other_user = get_user_model().objects.create_user(username="service-safe-other")
        own_unknown = Category.objects.get(user=user, name="Unknown")
        tx = Transaction.objects.create(
            user=other_user,
            date=date(2026, 6, 20),
            booking_date=date(2026, 6, 20),
            merchant="SERVICE CHECK MERCHANT",
            description="Service validation",
            amount="-6.00",
            transaction_number="SAFE-1",
            category=Category.objects.get(user=other_user, name="Unknown"),
        )

        with self.assertRaises(PermissionDenied):
            apply_category_correction(user=user, transaction=tx, category=own_unknown)

    def test_rejects_category_owned_by_another_user(self) -> None:
        user = get_user_model().objects.create_user(username="service-safe-user-two")
        other_user = get_user_model().objects.create_user(username="service-safe-other-two")
        own_unknown = Category.objects.get(user=user, name="Unknown")
        foreign_health = Category.objects.get(user=other_user, name="Health")
        tx = Transaction.objects.create(
            user=user,
            date=date(2026, 6, 21),
            booking_date=date(2026, 6, 21),
            merchant="SERVICE CHECK CATEGORY",
            description="Service validation category",
            amount="-7.00",
            transaction_number="SAFE-2",
            category=own_unknown,
        )

        with self.assertRaises(PermissionDenied):
            apply_category_correction(user=user, transaction=tx, category=foreign_health)


class PaginationAndFilterSortTests(TestCase):
    """Integration tests for pagination with filtering and sorting."""

    def setUp(self) -> None:
        """Create test user and transactions."""
        self.user = get_user_model().objects.create_user(
            username="pagination-user",
            password="testpass123",  # noqa: S106
        )
        self.client.login(username="pagination-user", password="testpass123")  # noqa: S106

        # Get categories
        self.food_category = Category.objects.get(user=self.user, name="Food and Household Chemicals")
        self.transport_category = Category.objects.get(user=self.user, name="Transportation")

        # Create 120 test transactions (will span 3 pages at 50 per page)
        base_amount = Decimal("100.00")
        for i in range(120):
            Transaction.objects.create(
                user=self.user,
                date=date(2026, 6, 1 + (i % 28)),
                booking_date=date(2026, 6, 1 + (i % 28)),
                merchant=f"MERCHANT-{i}",
                description=f"Transaction {i}",
                amount=base_amount - Decimal(str(i)),
                transaction_number=f"TX-{i:03d}",
                category=self.food_category if i % 2 == 0 else self.transport_category,
            )

    def test_pagination_with_filter_and_sort_combination(self) -> None:
        """Test that filter, sort, and pagination work together."""
        response = self.client.get(
            reverse("transactions:list"),
            {"category": "Food and Household Chemicals", "sort_by": "date", "sort_order": "desc", "page": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["page_obj"].number, 1)
        # Should have 60 food transactions (120 / 2), spanning 2 pages at 50 per page
        self.assertEqual(response.context["paginator"].count, 60)

    def test_pagination_reset_on_invalid_page_number(self) -> None:
        """Test that requesting page > num_pages resets to page 1."""
        response = self.client.get(
            reverse("transactions:list"),
            {"category": "Food and Household Chemicals", "page": 99},
        )

        self.assertEqual(response.status_code, 200)
        # Should reset to page 1 instead of 404
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_pagination_with_sort_order_toggle(self) -> None:
        """Test pagination with different sort orders."""
        response_asc = self.client.get(
            reverse("transactions:list"),
            {"sort_by": "amount", "sort_order": "asc", "page": 1},
        )
        response_desc = self.client.get(
            reverse("transactions:list"),
            {"sort_by": "amount", "sort_order": "desc", "page": 1},
        )

        self.assertEqual(response_asc.status_code, 200)
        self.assertEqual(response_desc.status_code, 200)

        # Verify different sort orders
        asc_first = response_asc.context["page_obj"].object_list[0]
        desc_first = response_desc.context["page_obj"].object_list[0]
        self.assertNotEqual(asc_first.pk, desc_first.pk)

    def test_filter_sort_and_pagination_state_preserved_in_context(self) -> None:
        """Test that filter, sort, and page state is preserved in template context."""
        response = self.client.get(
            reverse("transactions:list"),
            {"category": "Transportation", "sort_by": "date", "sort_order": "desc", "page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_category"], "Transportation")
        self.assertEqual(response.context["sort_by"], "date")
        self.assertEqual(response.context["sort_order"], "desc")
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_filter_change_from_high_page_resets_to_first_page(self) -> None:
        """Test switching to a smaller filtered set resets page to 1."""
        initial_response = self.client.get(reverse("transactions:list"), {"page": 3})
        self.assertEqual(initial_response.status_code, 200)
        self.assertEqual(initial_response.context["page_obj"].number, 3)

        filtered_response = self.client.get(
            reverse("transactions:list"),
            {"category": "Transportation", "page": 3},
        )

        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(filtered_response.context["page_obj"].number, 1)
        self.assertEqual(filtered_response.context["selected_category"], "Transportation")

    def test_same_params_request_returns_consistent_state(self) -> None:
        """Test repeated same-param requests preserve identical state."""
        params = {"category": "Food and Household Chemicals", "sort_by": "date", "sort_order": "desc", "page": 1}
        first_response = self.client.get(reverse("transactions:list"), params)
        second_response = self.client.get(reverse("transactions:list"), params)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        first_ids = [tx.pk for tx in first_response.context["page_obj"].object_list]
        second_ids = [tx.pk for tx in second_response.context["page_obj"].object_list]

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(second_response.context["selected_category"], "Food and Household Chemicals")
        self.assertEqual(second_response.context["sort_by"], "date")
        self.assertEqual(second_response.context["sort_order"], "desc")
        self.assertEqual(second_response.context["page_obj"].number, 1)

    def test_no_filter_sort_default_to_all_ascending(self) -> None:
        """Test that no filter/sort params show all transactions in default order."""
        response = self.client.get(reverse("transactions:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_category"], "")
        self.assertEqual(response.context["sort_by"], "")
        self.assertEqual(response.context["sort_order"], "asc")
        self.assertEqual(response.context["paginator"].count, 120)

    def test_cross_user_isolation_with_pagination(self) -> None:
        """Test that pagination respects user isolation."""
        other_user = get_user_model().objects.create_user(
            username="pagination-other-user",
            password="testpass123",  # noqa: S106
        )

        # Create transactions for other user
        for i in range(20):
            Transaction.objects.create(
                user=other_user,
                date=date(2026, 6, 1),
                booking_date=date(2026, 6, 1),
                merchant=f"OTHER-MERCHANT-{i}",
                description=f"Other transaction {i}",
                amount=Decimal("10.00"),
                transaction_number=f"OTHER-{i}",
                category=Category.objects.get(user=other_user, name="Food and Household Chemicals"),
            )

        response = self.client.get(reverse("transactions:list"))

        # Should only see this user's 120 transactions, not the other user's 20
        self.assertEqual(response.context["paginator"].count, 120)
