"""Forms for budgets app."""

from typing import Any, Self

from django import forms
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Q

from budgets.models import Budget, BudgetCategoryAllocation
from categories.forms import grouped_category_choices
from categories.models import Category


class BudgetForm(forms.ModelForm):
    """Form for Budget model with date range validation and overlap checking."""

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
        # Update date fields to accept dd/mm/yyyy format from Polish datepicker
        self.fields["start_date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]  # type: ignore[attr-defined]
        self.fields["end_date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]  # type: ignore[attr-defined]

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


class BudgetAllocationForm(forms.ModelForm):  # type: ignore[type-arg]
    """Form for individual budget category allocations."""

    class Meta:
        model = BudgetCategoryAllocation
        fields = ["category", "amount"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }

    def __init__(self: "BudgetAllocationForm", *args: Any, user: Any = None, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        if user:
            # Filter categories to only those owned by the user
            categories = Category.objects.filter(user=user)
            self.fields["category"].queryset = categories  # type: ignore[attr-defined]
            # Presentational only: ModelChoiceField still validates against the queryset above.
            self.fields["category"].choices = grouped_category_choices(  # type: ignore[attr-defined]
                categories,
                empty_label=self.fields["category"].empty_label,  # type: ignore[attr-defined]
            )


# Inline formset for BudgetCategoryAllocation
BudgetAllocationFormSet = forms.inlineformset_factory(
    Budget,
    BudgetCategoryAllocation,
    form=BudgetAllocationForm,
    extra=0,
    can_delete=True,
)
