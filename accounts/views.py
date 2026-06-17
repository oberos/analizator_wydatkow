from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
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

FIXED_COLOR_BY_CATEGORY: dict[str, str] = {
    "Beauty": "#d63384",
    "Bills": "#0d6efd",
    "Clothing and Footwear": "#fd7e14",
    "Finance": "#6f42c1",
    "Food and Household Chemicals": "#198754",
    "Health": "#dc3545",
    "Home": "#0dcaf0",
    "Recreation": "#20c997",
    "Restaurants": "#6610f2",
    "Savings": "#adb5bd",
    "Sports": "#795548",
    "Transportation": "#ffc107",
    "Unknown": "#ffca2c",
    "Uncategorized": "#6c757d",
}
FALLBACK_CHART_PALETTE: tuple[str, ...] = (
    "#0d6efd",
    "#20c997",
    "#fd7e14",
    "#6610f2",
    "#198754",
    "#dc3545",
    "#0dcaf0",
    "#adb5bd",
)


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


def _color_for_category(category_name: str) -> str:
    """Return a deterministic display color for a category name."""
    if category_name in FIXED_COLOR_BY_CATEGORY:
        return FIXED_COLOR_BY_CATEGORY[category_name]

    hash_value = sum(ord(char) for char in category_name)
    return FALLBACK_CHART_PALETTE[hash_value % len(FALLBACK_CHART_PALETTE)]


def _build_dashboard_chart_payload(category_summary: list[dict[str, object]]) -> dict[str, object]:
    """Return chart-safe payload derived from dashboard summary rows."""
    chart_labels: list[str] = []
    chart_values: list[float] = []
    chart_colors: list[str] = []
    excluded_non_positive_categories: list[str] = []

    for row in category_summary:
        category_name = row.get("category_name")
        total_amount = row.get("total_amount")
        if not isinstance(category_name, str) or not isinstance(total_amount, Decimal):
            if settings.DEBUG:
                raise AssertionError(f"Unexpected summary row shape for dashboard chart payload: {row!r}")
            continue

        if total_amount <= 0:
            excluded_non_positive_categories.append(category_name)
            continue

        chart_labels.append(category_name)
        chart_values.append(float(total_amount))
        chart_colors.append(_color_for_category(category_name))

    return {
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "chart_colors": chart_colors,
        "chart_excluded_non_positive_categories": excluded_non_positive_categories,
        "chart_is_renderable": bool(chart_values),
    }


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard view for authenticated users."""
    user = request.user
    assert isinstance(user, AbstractUser)  # @login_required guarantees this

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

    category_summary = get_user_category_summary(
        user=user,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )
    chart_payload = _build_dashboard_chart_payload(category_summary)

    context = {
        "category_summary": category_summary,
        "has_any_transactions": Transaction.objects.filter(user=user).exists(),
        "date_range_form": date_range_form,
        "selected_start_date": selected_start_date,
        "selected_end_date": selected_end_date,
        **chart_payload,
    }
    return render(request, "dashboard.html", context)
