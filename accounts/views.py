from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import AbstractUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from transactions.forms import DashboardDateRangeForm
from transactions.models import Transaction
from transactions.summary import get_user_category_summary


class RegisterView(CreateView):
    """User registration view using Django's built-in UserCreationForm."""

    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")


def _default_dashboard_range() -> tuple[date, date]:
    """Return default dashboard date window (last 30 days, inclusive)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard view for authenticated users."""
    user = request.user
    if not isinstance(user, AbstractUser):
        msg = "Authenticated request user has invalid type."
        raise TypeError(msg)

    default_start_date, default_end_date = _default_dashboard_range()
    has_date_query = "start_date" in request.GET or "end_date" in request.GET
    if has_date_query:
        date_range_form = DashboardDateRangeForm(request.GET)
    else:
        date_range_form = DashboardDateRangeForm(
            initial={"start_date": default_start_date, "end_date": default_end_date}
        )

    if date_range_form.is_bound and date_range_form.is_valid():
        selected_start_date = date_range_form.cleaned_data["start_date"]
        selected_end_date = date_range_form.cleaned_data["end_date"]
    else:
        selected_start_date = default_start_date
        selected_end_date = default_end_date

    context = {
        "category_summary": get_user_category_summary(
            user=user,
            start_date=selected_start_date,
            end_date=selected_end_date,
        ),
        "has_any_transactions": Transaction.objects.filter(user=user).exists(),
        "date_range_form": date_range_form,
        "selected_start_date": selected_start_date,
        "selected_end_date": selected_end_date,
    }
    return render(request, "dashboard.html", context)
