"""Forms for budgets app."""

from typing import Any, Self

from django import forms
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Q

from budgets.models import Budget, BudgetCategoryAllocation


class BudgetForm(forms.ModelForm):
    """Form for Budget model with date range validation and overlap checking."""

    DATE_INPUT_FORMATS = ["%d/%m/%Y", "%Y-%m-%d"]

    class Meta:
        model = Budget
        fields = ["name", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "class": "form-control js-date-picker",
                    "placeholder": "DD/MM/YYYY",
                    "autocomplete": "off",
                },
            ),
            "end_date": forms.DateInput(
                format="%d/%m/%Y",
                attrs={
                    "class": "form-control js-date-picker",
                    "placeholder": "DD/MM/YYYY",
                    "autocomplete": "off",
                },
            ),
        }

    def __init__(self: Self, *args: Any, user: AbstractUser | None = None, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize form with user for overlap validation."""
        self.user = user
        super().__init__(*args, **kwargs)
        # Update start_date field to use custom input formats
        self.fields["start_date"].input_formats = self.DATE_INPUT_FORMATS  # type: ignore[attr-defined]
        self.fields["end_date"].input_formats = self.DATE_INPUT_FORMATS  # type: ignore[attr-defined]

    def clean(self: Self) -> dict[str, Any]:
        """Validate date ordering and check for overlapping budgets."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Validate start_date <= end_date
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be on or before end date.")

        # Check for overlapping budgets for the same user
        if self.user and start_date and end_date:
            overlapping = Budget.objects.filter(user=self.user).filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            )
            # Exclude current instance if this is an update
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError("Budget dates overlap with an existing budget.")

        return cleaned_data


# Inline formset for BudgetCategoryAllocation
BudgetAllocationFormSet = forms.inlineformset_factory(
    Budget,
    BudgetCategoryAllocation,
    fields=["category", "amount"],
    extra=3,
    can_delete=True,
    widgets={
        "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
    },
)
