"""Forms for transactions app."""

from typing import Self, cast

from django import forms
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from categories.models import Category


class CSVUploadForm(forms.Form):
    """Form for uploading ING CSV file."""

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    csv_file = forms.FileField(
        label="ING CSV File",
        help_text="Export from ING Bank Śląski",
    )

    def clean_csv_file(
        self: Self,
    ) -> forms.FileField:
        """Validate uploaded CSV file type and size."""
        csv_file = self.cleaned_data["csv_file"]

        if not csv_file.name.lower().endswith(".csv"):
            raise ValidationError("Please upload a .csv file.")

        if csv_file.size > self.MAX_FILE_SIZE:
            raise ValidationError("File is too large. Maximum allowed size is 5 MB.")

        return csv_file


class TransactionCategoryCorrectionForm(forms.Form):
    """Form for correcting a transaction category within user's own scope."""

    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label="Uncategorized",
    )

    def __init__(self: Self, *args, user: AbstractUser, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        category_field = cast(forms.ModelChoiceField, self.fields["category"])
        category_field.queryset = Category.objects.filter(user=user)
