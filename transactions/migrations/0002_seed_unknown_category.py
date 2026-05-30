"""Seed 'Unknown' category for existing users."""

from django.conf import settings
from django.db import migrations


def seed_unknown_category(apps, schema_editor):
    """Create 'Unknown' category for all existing users who don't have it."""
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app_label, user_model_name)
    Category = apps.get_model("categories", "Category")

    for user in User.objects.all():
        Category.objects.get_or_create(name="Unknown", user=user)


def reverse_seed_unknown_category(apps, schema_editor):
    """No-op reverse migration - don't delete user data."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0001_initial"),
        ("categories", "0002_seed_predefined_categories"),
    ]

    operations = [
        migrations.RunPython(seed_unknown_category, reverse_seed_unknown_category),
    ]
