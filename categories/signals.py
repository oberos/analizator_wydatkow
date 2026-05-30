from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from categories.models import Category

User = get_user_model()

PREDEFINED_CATEGORIES = [
    "Groceries",
    "Transport",
    "Entertainment",
    "Bills",
    "Health",
]


@receiver(post_save, sender=User)
def create_predefined_categories(
    sender: type, instance: User, created: bool, **kwargs  # noqa: ANN003, ARG001
) -> None:
    """Create predefined categories for newly registered users."""
    if created:
        Category.objects.bulk_create(
            [Category(name=name, user=instance) for name in PREDEFINED_CATEGORIES],
            ignore_conflicts=True,
        )
