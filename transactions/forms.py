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


class DashboardDateRangeForm(forms.Form):
    """Form for filtering dashboard summary by date range."""

    DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]

    start_date = forms.DateField(
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control js-date-picker",
                "placeholder": "DD/MM/YYYY",
                "autocomplete": "off",
            },
        ),
    )
    end_date = forms.DateField(
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "class": "form-control js-date-picker",
                "placeholder": "DD/MM/YYYY",
                "autocomplete": "off",
            },
        ),
    )

    def clean(self: Self) -> dict[str, object]:
        """Validate that start date is not after end date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be on or before end date.")

        return cleaned_data
