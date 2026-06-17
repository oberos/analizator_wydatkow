from django.db import migrations
from django.db.models import F


def _ensure_ownership_invariants(apps, schema_editor) -> None:
    transaction_model = apps.get_model("transactions", "Transaction")
    mapping_model = apps.get_model("transactions", "MerchantCategoryMapping")

    transaction_mismatches = list(
        transaction_model.objects.filter(category__isnull=False)
        .exclude(user_id=F("category__user_id"))
        .values_list("id", "user_id", "category_id", "category__user_id")[:10]
    )
    mapping_mismatches = list(
        mapping_model.objects.exclude(user_id=F("category__user_id")).values_list(
            "id", "user_id", "category_id", "category__user_id"
        )[:10]
    )

    if not transaction_mismatches and not mapping_mismatches:
        return

    transaction_lines = [
        f"tx_id={row[0]} tx_user={row[1]} category_id={row[2]} category_user={row[3]}" for row in transaction_mismatches
    ]
    mapping_lines = [
        f"mapping_id={row[0]} mapping_user={row[1]} category_id={row[2]} category_user={row[3]}"
        for row in mapping_mismatches
    ]
    preview = "\n".join(
        [
            "Transaction mismatches (up to 10):",
            *(transaction_lines or ["- none"]),
            "",
            "MerchantCategoryMapping mismatches (up to 10):",
            *(mapping_lines or ["- none"]),
        ]
    )

    raise RuntimeError(
        "Access-isolation hardening blocked migration because cross-user ownership mismatches were found.\n\n"
        f"{preview}\n\n"
        "Remediate the mismatches first, then rerun migrate. Example workflow:\n"
        "  1) Open Django shell.\n"
        "  2) For each offending Transaction row, either set category to NULL or move it to a category owned by the same user.\n"
        "  3) For each offending MerchantCategoryMapping row, delete or re-point it to a category owned by mapping.user.\n"
        "  4) Re-run: pdm run python manage.py migrate"
    )


def _noop_reverse(apps, schema_editor) -> None:
    return


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0005_transaction_transaction_user_id_c1e6a9_idx"),
    ]

    operations = [
        migrations.RunPython(_ensure_ownership_invariants, _noop_reverse),
    ]
