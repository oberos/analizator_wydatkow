from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


class RegisterView(CreateView):
    """User registration view using Django's built-in UserCreationForm."""

    form_class = UserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")
