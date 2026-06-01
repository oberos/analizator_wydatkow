from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from categories.models import Category

from .mappings import PREDEFINED_MAPPINGS
from .models import MerchantCategoryMapping

User = get_user_model()

@receiver(post_save, sender=User)
def create_predefined_mappings(
    sender: type,
    instance: User,  # type: ignore
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Create predefined merchant mappings for newly registered users."""
    if created:
        user_categories = {cat.name: cat for cat in Category.objects.filter(user=instance)}
        missing_categories = sorted(set(PREDEFINED_MAPPINGS.values()) - set(user_categories))
        for category_name in missing_categories:
            category, _ = Category.objects.get_or_create(user=instance, name=category_name)
            user_categories[category_name] = category

        mappings_to_create = []
        for merchant, category_name in PREDEFINED_MAPPINGS.items():
            mappings_to_create.append(
                MerchantCategoryMapping(
                    user=instance,
                    normalized_merchant=merchant,
                    category=user_categories[category_name],
                )
            )
        MerchantCategoryMapping.objects.bulk_create(
            mappings_to_create,
            ignore_conflicts=True,
        )
