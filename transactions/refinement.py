"""Category correction services for imported transactions."""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied

from categories.models import Category

from .categorization import normalize_merchant
from .models import MerchantCategoryMapping, Transaction


def _should_remove_mapping(category: Category | None) -> bool:
    """Return True when correction should clear learned mapping."""
    return category is None or category.name == "Unknown"


def _sync_merchant_mapping(
    *,
    user: AbstractUser,
    merchant: str,
    category: Category | None,
) -> None:
    """Create/update or remove merchant mapping based on correction result."""
    normalized_merchant = normalize_merchant(merchant)
    if not normalized_merchant:
        return

    if _should_remove_mapping(category):
        MerchantCategoryMapping.objects.filter(
            user=user,
            normalized_merchant=normalized_merchant,
        ).delete()
        return

    MerchantCategoryMapping.objects.update_or_create(
        user=user,
        normalized_merchant=normalized_merchant,
        defaults={"category": category},
    )


def apply_category_correction(
    *,
    user: AbstractUser,
    transaction: Transaction,
    category: Category | None,
) -> Transaction:
    """Persist transaction category correction and sync learning mapping."""
    if transaction.user != user:
        raise PermissionDenied("Cannot modify a transaction owned by another user.")
    if category is not None and category.user != user:
        raise PermissionDenied("Cannot assign a category owned by another user.")

    transaction.category = category
    transaction.save(update_fields=["category"])

    _sync_merchant_mapping(
        user=user,
        merchant=transaction.merchant,
        category=category,
    )
    return transaction
