from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from categories.models import Category

User = get_user_model()

PREDEFINED_CATEGORIES: dict[str, str] = {
    "Beauty": "#d63384",
    "Bills": "#0d6efd",
    "Clothing and Footwear": "#fd7e14",
    "Finance": "#6f42c1",
    "Food and Household Chemicals": "#198754",
    "Health": "#dc3545",
    "Home": "#0dcaf0",
    "Recreation": "#20c997",
    "Restaurants": "#6610f2",
    "Savings": "#adb5bd",
    "Sports": "#795548",
    "Transportation": "#ffc107",
    "Unknown": "#ffca2c",
    "Uncategorized": "#6c757d",
}


@receiver(post_save, sender=User)
def create_predefined_categories(
    sender: type,
    instance: User,  # type: ignore
    created: bool,
    **kwargs,  # noqa: ANN003, ARG001
) -> None:
    """Create predefined categories for newly registered users."""
    if created:
        Category.objects.bulk_create(
            [
                Category(
                    name=name,
                    color=color,
                    user=instance,
                )
                for name, color in PREDEFINED_CATEGORIES.items()
            ],
            ignore_conflicts=True,
        )
