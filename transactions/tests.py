from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from categories.models import Category
from categories.signals import PREDEFINED_CATEGORIES

from .categorization import categorize_transaction, normalize_merchant
from .mappings import PREDEFINED_CATEGORY_GROUPS, PREDEFINED_MAPPINGS
from .models import MerchantCategoryMapping, Transaction


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
        self.assertEqual(category.name, "Transportation")


class ImportFlowAndRolloutTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="import-user")
        self.client.force_login(self.user)

    def _build_ing_csv(self) -> bytes:
        rows = [
            "Data transakcji;Data księgowania;Dane kontrahenta;Tytuł;"
            "Kwota transakcji (waluta rachunku);Nr transakcji",
            "2026-05-01;2026-05-01;BIEDRONKA;Zakupy spozywcze;-120,50;TX-1",
            "2026-05-02;2026-05-02;UNMAPPED MERCHANT;Zakup testowy;-15,99;TX-2",
        ]
        return "\n".join(rows).encode("windows-1250")

    def test_upload_flow_categorizes_and_skips_duplicates(self) -> None:
        upload = SimpleUploadedFile("ing.csv", self._build_ing_csv(), content_type="text/csv")
        response = self.client.post(reverse("transactions:upload"), {"csv_file": upload})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))

        imported = Transaction.objects.filter(user=self.user).order_by("transaction_number")
        self.assertEqual(imported.count(), 2)

        category_by_tx_number = {tx.transaction_number: tx.category.name for tx in imported}
        self.assertEqual(category_by_tx_number["TX-1"], "Food and Household Chemicals")
        self.assertEqual(category_by_tx_number["TX-2"], "Unknown")

        second_upload = SimpleUploadedFile("ing.csv", self._build_ing_csv(), content_type="text/csv")
        self.client.post(reverse("transactions:upload"), {"csv_file": second_upload})
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 2)

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
        self.assertEqual(response.url, reverse("transactions:list"))
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

    def test_set_category_updates_transaction_and_creates_mapping(self) -> None:
        unknown_category = Category.objects.get(user=self.user, name="Unknown")
        target_category = Category.objects.get(user=self.user, name="Health")
        tx = self._create_transaction("REF-1", "TEST MERCHANT", unknown_category)

        response = self.client.post(
            reverse("transactions:set_category", kwargs={"pk": tx.pk}),
            {"category": str(target_category.pk)},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("transactions:list"))

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
        normalized_merchant = normalize_merchant(tx.merchant)
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
        self.assertEqual(response.url, reverse("transactions:list"))

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
        normalized_merchant = normalize_merchant(tx.merchant)
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
        self.assertEqual(response.url, reverse("transactions:list"))

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
        self.assertEqual(response.url, reverse("transactions:list"))

        tx.refresh_from_db()
        self.assertEqual(tx.category, unknown_category)
        self.assertFalse(
            MerchantCategoryMapping.objects.filter(
                user=self.user,
                normalized_merchant=normalize_merchant(tx.merchant),
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
        self.assertEqual(response.url, reverse("transactions:list"))

        other_tx.refresh_from_db()
        self.assertEqual(other_tx.category, other_unknown_category)
