from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import AbstractUser
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from transactions.summary import get_user_category_summary


class RegisterView(CreateView):
    """User registration view using Django's built-in UserCreationForm."""

    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard view for authenticated users."""
    user = request.user
    if not isinstance(user, AbstractUser):
        msg = "Authenticated request user has invalid type."
        raise TypeError(msg)
    context = {
        "category_summary": get_user_category_summary(user),
    }
    return render(request, "dashboard.html", context)
