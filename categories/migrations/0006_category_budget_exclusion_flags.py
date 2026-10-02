from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("categories", "0005_category_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="is_income",
            field=models.BooleanField(
                default=False,
                help_text="Exclude this category from budget spend totals because it represents incoming money.",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="is_irrelevant",
            field=models.BooleanField(
                default=False,
                help_text="Exclude this category from budget spend totals because it is not part of the spending budget.",
            ),
        ),
    ]
