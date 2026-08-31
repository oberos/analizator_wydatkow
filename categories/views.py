from typing import Any, Self

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from categories.forms import CategoryForm
from categories.models import Category


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories for the logged-in user."""

    model = Category
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self: Self) -> QuerySet[Category]:
        return (
            Category.objects.filter(user=self.request.user)
            .select_related("parent")
            .prefetch_related("subcategories")
            .order_by("parent__name", "name")
        )


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new category for the logged-in user."""

    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def get_form_kwargs(self: Self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self: Self, form: CategoryForm) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing category owned by the logged-in user."""

    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self: Self) -> QuerySet[Category]:
        return Category.objects.filter(user=self.request.user)

    def get_form_kwargs(self: Self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a category owned by the logged-in user."""

    model = Category
    template_name = "categories/category_confirm_delete.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self: Self) -> QuerySet[Category]:
        return Category.objects.filter(user=self.request.user)

    def get_context_data(self: Self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        context = super().get_context_data(**kwargs)
        context["subcategory_count"] = self.object.subcategories.count()  # type: ignore[attr-defined]
        return context
