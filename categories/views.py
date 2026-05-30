from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from categories.models import Category


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories for the logged-in user."""

    model = Category
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self) -> QuerySet[Category]:
        return Category.objects.filter(user=self.request.user)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new category for the logged-in user."""

    model = Category
    fields = ["name"]
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def form_valid(self, form) -> HttpResponse:  # noqa: ANN001
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing category owned by the logged-in user."""

    model = Category
    fields = ["name"]
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self) -> QuerySet[Category]:
        return Category.objects.filter(user=self.request.user)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a category owned by the logged-in user."""

    model = Category
    template_name = "categories/category_confirm_delete.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self) -> QuerySet[Category]:
        return Category.objects.filter(user=self.request.user)
