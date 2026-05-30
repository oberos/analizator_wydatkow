"""Forms for transactions app."""

from django import forms


class CSVUploadForm(forms.Form):
    """Form for uploading ING CSV file."""

    csv_file = forms.FileField(
        label="ING CSV File",
        help_text="Export from ING Bank Śląski",
    )
