"""Forms for transactions app."""

from django import forms
from django.core.exceptions import ValidationError


class CSVUploadForm(forms.Form):
    """Form for uploading ING CSV file."""

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    csv_file = forms.FileField(
        label="ING CSV File",
        help_text="Export from ING Bank Śląski",
    )

    def clean_csv_file(self):  # noqa: ANN201
        """Validate uploaded CSV file type and size."""
        csv_file = self.cleaned_data["csv_file"]

        if not csv_file.name.lower().endswith(".csv"):
            raise ValidationError("Please upload a .csv file.")

        if csv_file.size > self.MAX_FILE_SIZE:
            raise ValidationError("File is too large. Maximum allowed size is 5 MB.")

        return csv_file
