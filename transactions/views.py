"""Views for transactions app."""

from typing import Self

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, Page, Paginator
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView, ListView

from categories.models import Category

from .categorization import categorize_transactions
from .csv_parser import CSVParseError, parse_ing_csv
from .forms import CSVUploadForm, TransactionCategoryCorrectionForm
from .models import Transaction
from .refinement import apply_category_correction


class TransactionListView(LoginRequiredMixin, ListView):
    """Display all user's transactions with their categories."""

    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self: Self):  # noqa: ANN201
        """Filter transactions to current user only, with optional filtering and sorting."""
        queryset = Transaction.objects.filter(user=self.request.user).select_related("category")

        # Apply category filter if provided
        category = self.request.GET.get("category", "").strip()
        if category:
            queryset = queryset.filter(category__name=category)

        # Apply sorting if provided
        sort_by = self.request.GET.get("sort_by", "").strip()
        sort_order = self.request.GET.get("sort_order", "asc").strip()

        if sort_by in ("date", "amount"):
            sort_field = "date" if sort_by == "date" else "amount"
            if sort_order == "desc":
                sort_field = f"-{sort_field}"
            queryset = queryset.order_by(sort_field)

        return queryset

    def paginate_queryset(  # noqa: ANN201
        self: Self,
        queryset: QuerySet[Transaction],
        page_size: int,
    ) -> tuple[Paginator, Page, QuerySet[Transaction], bool]:  # noqa: ANN001
        """Override pagination to reset to page 1 if requested page is too high."""
        paginator = Paginator(queryset, page_size)
        page_number = self.request.GET.get(self.page_kwarg, 1)

        try:
            page = paginator.page(page_number)
        except EmptyPage:
            # Reset to page 1 instead of raising 404
            page = paginator.page(1)

        return (paginator, page, page.object_list, page.has_other_pages())

    def get_context_data(self: Self, **kwargs):  # noqa: ANN003, ANN201
        """Add upload form, filter/sort state, and categories to context."""
        context = super().get_context_data(**kwargs)
        context["upload_form"] = CSVUploadForm()
        context["category_options"] = Category.objects.filter(user=self.request.user).order_by("name")

        # Pass filter/sort state to template
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["sort_by"] = self.request.GET.get("sort_by", "").strip()
        context["sort_order"] = self.request.GET.get("sort_order", "asc").strip()

        return context


class CSVUploadView(LoginRequiredMixin, FormView):
    """Handle CSV file upload, parse, categorize, and save transactions."""

    form_class = CSVUploadForm
    template_name = "transactions/transaction_list.html"
    success_url = "/transactions/"

    def form_valid(self: Self, form: CSVUploadForm) -> HttpResponse:
        """Process the uploaded CSV file."""
        csv_file = form.cleaned_data["csv_file"]
        file_content = csv_file.read()

        try:
            # Parse CSV
            parsed_transactions = parse_ing_csv(file_content)

            if not parsed_transactions:
                messages.warning(self.request, "No transactions found in the CSV file.")
                return redirect("transactions:list")

            # Categorize transactions
            categorized = categorize_transactions(self.request.user, parsed_transactions)  # pyright: ignore[reportArgumentType]

            # Get "Unknown" category for uncategorized transactions
            unknown_category, _ = Category.objects.get_or_create(user=self.request.user, name="Unknown")

            transactions_to_create = [
                Transaction(
                    user=self.request.user,
                    date=parsed_tx.date,
                    booking_date=parsed_tx.booking_date,
                    merchant=parsed_tx.merchant,
                    description=parsed_tx.description,
                    amount=parsed_tx.amount,
                    transaction_number=parsed_tx.transaction_number,
                    category=category if category else unknown_category,
                )
                for parsed_tx, category in categorized
            ]

            before_count = Transaction.objects.filter(user=self.request.user).count()
            with transaction.atomic():
                Transaction.objects.bulk_create(
                    transactions_to_create,
                    ignore_conflicts=True,
                )
            after_count = Transaction.objects.filter(user=self.request.user).count()

            imported_count = after_count - before_count
            skipped_count = len(transactions_to_create) - imported_count

            messages.success(
                self.request,
                f"Imported {imported_count} transactions, skipped {skipped_count} duplicates.",
            )

        except CSVParseError as e:
            messages.error(self.request, f"CSV parsing error: {e}")

        return redirect("transactions:list")

    def form_invalid(self: Self, form: CSVUploadForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(self.request, "Please select a valid CSV file.")
        return redirect("transactions:list")


class DeleteAllTransactionsView(LoginRequiredMixin, View):
    """Delete all user's transactions for fresh start."""

    def post(self: Self, request: HttpRequest) -> HttpResponse:
        """Delete all transactions for current user."""
        count, _ = Transaction.objects.filter(user=request.user).delete()
        messages.success(request, f"Deleted {count} transactions.")
        return redirect("transactions:list")


class TransactionSetCategoryView(LoginRequiredMixin, View):
    """Update category for one user-owned transaction."""

    def post(self: Self, request: HttpRequest, pk: int) -> HttpResponse:
        """Handle single-transaction category correction."""
        tx = Transaction.objects.filter(user=request.user, pk=pk).first()
        if tx is None:
            messages.error(request, "Transaction not found or access denied.")
            return redirect("transactions:list")

        form = TransactionCategoryCorrectionForm(request.POST, user=request.user)  # pyright: ignore[reportArgumentType]
        if not form.is_valid():
            messages.error(request, "Selected category is invalid for your account.")
            return redirect("transactions:list")

        category = form.cleaned_data["category"]

        with transaction.atomic():
            apply_category_correction(
                user=request.user,  # pyright: ignore[reportArgumentType]
                transaction=tx,
                category=category,
            )

        category_label = category.name if category else "Uncategorized"
        messages.success(request, f"Updated category to {category_label}.")
        return redirect("transactions:list")
