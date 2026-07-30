from typing import Any, Self

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from budgets.forms import BudgetAllocationForm, BudgetAllocationFormSet, BudgetForm
from budgets.models import Budget, BudgetCategoryAllocation
from budgets.summary import get_budget_comparison


class BudgetListView(LoginRequiredMixin, ListView):  # type: ignore[type-arg]
    """List all budgets for the logged-in user with summary cards."""

    model = Budget
    template_name = "budgets/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self: Self) -> QuerySet[Budget]:
        return Budget.objects.filter(user=self.request.user).order_by("-start_date")

    def get_context_data(self: Self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        context = super().get_context_data(**kwargs)
        # Add comparison data for each budget to show in cards
        budgets_with_summary = []
        for budget in context["budgets"]:
            comparison_data = get_budget_comparison(budget)
            total_budgeted = sum(item["budgeted_amount"] for item in comparison_data)
            total_actual = sum(item["actual_amount"] for item in comparison_data)
            budgets_with_summary.append(
                {
                    "budget": budget,
                    "total_budgeted": total_budgeted,
                    "total_actual": total_actual,
                    "total_difference": total_budgeted - total_actual,
                }
            )
        context["budgets_with_summary"] = budgets_with_summary
        return context


class BudgetDetailView(LoginRequiredMixin, DetailView):  # type: ignore[type-arg]
    """Show detailed per-category breakdown for a budget."""

    model = Budget
    template_name = "budgets/budget_detail.html"
    context_object_name = "budget"

    def get_queryset(self: Self) -> QuerySet[Budget]:
        return Budget.objects.filter(user=self.request.user)

    def get_context_data(self: Self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        context = super().get_context_data(**kwargs)
        context["comparison_data"] = get_budget_comparison(self.object)  # type: ignore[attr-defined]
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):  # type: ignore[type-arg]
    """Create a new budget for the logged-in user."""

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"

    def get_form_kwargs(self: Self) -> dict[str, Any]:  # noqa: ANN401
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self: Self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self: Self) -> str:
        return reverse("budgets:edit", kwargs={"pk": self.object.pk})  # type: ignore[attr-defined]


class BudgetUpdateView(LoginRequiredMixin, UpdateView):  # type: ignore[type-arg]
    """Update an existing budget and manage category allocations."""

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"

    def get_queryset(self: Self) -> QuerySet[Budget]:
        return Budget.objects.filter(user=self.request.user)

    def get_form_kwargs(self: Self) -> dict[str, Any]:  # noqa: ANN401
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self: Self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = BudgetAllocationFormSet(
                self.request.POST, instance=self.object, form_kwargs={"user": self.request.user}
            )
        else:
            # Check if this budget already has allocations
            existing_allocations = BudgetCategoryAllocation.objects.filter(budget=self.object)
            has_allocations = existing_allocations.exists()

            if has_allocations:
                # Budget already configured - just show existing allocations + 1 empty for adding
                allocation_formset_class = forms.inlineformset_factory(
                    Budget,
                    BudgetCategoryAllocation,
                    form=BudgetAllocationForm,
                    extra=1,
                    can_delete=True,
                )
                formset = allocation_formset_class(
                    instance=self.object,
                    form_kwargs={"user": self.request.user},
                )
            else:
                # First time editing - pre-populate with all user categories
                from categories.models import Category

                all_categories = list(Category.objects.filter(user=self.request.user))
                initial_data = [{"category": cat, "amount": 0} for cat in all_categories]

                allocation_formset_class = forms.inlineformset_factory(
                    Budget,
                    BudgetCategoryAllocation,
                    form=BudgetAllocationForm,
                    extra=len(initial_data),
                    can_delete=True,
                )
                formset = allocation_formset_class(
                    instance=self.object,
                    form_kwargs={"user": self.request.user},
                    initial=initial_data,
                )

            context["formset"] = formset
            context["has_allocations"] = has_allocations
        return context

    def post(self: Self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: ANN401
        self.object = self.get_object()
        form = self.get_form()
        formset = BudgetAllocationFormSet(
            self.request.POST, instance=self.object, form_kwargs={"user": self.request.user}
        )

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        return self.form_invalid(form, formset)

    def form_valid(
        self: Self,
        form: BaseModelForm,
        formset: BudgetAllocationFormSet,  # type: ignore[type-arg]
    ) -> HttpResponse:
        form.instance.user = self.request.user
        self.object = form.save()
        formset.instance = self.object
        formset.save()
        return HttpResponse(
            status=302,
            headers={"Location": self.get_success_url()},
        )

    def form_invalid(
        self: Self,
        form: BaseModelForm,
        formset: BudgetAllocationFormSet,  # type: ignore[type-arg]
    ) -> HttpResponse:
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def get_success_url(self: Self) -> str:
        return reverse("budgets:detail", kwargs={"pk": self.object.pk})  # type: ignore[attr-defined]


class BudgetDeleteView(LoginRequiredMixin, DeleteView):  # type: ignore[type-arg]
    """Delete a budget owned by the logged-in user."""

    model = Budget
    template_name = "budgets/budget_confirm_delete.html"
    success_url = reverse_lazy("budgets:list")

    def get_queryset(self: Self) -> QuerySet[Budget]:
        return Budget.objects.filter(user=self.request.user)
