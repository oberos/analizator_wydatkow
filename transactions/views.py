"""Views for transactions app."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView, ListView

from categories.models import Category

from .categorization import categorize_transactions
from .csv_parser import CSVParseError, parse_ing_csv
from .forms import CSVUploadForm
from .models import Transaction


class TransactionListView(LoginRequiredMixin, ListView):
    """Display all user's transactions with their categories."""

    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):  # noqa: ANN201
        """Filter transactions to current user only."""
        return Transaction.objects.filter(user=self.request.user).select_related("category")

    def get_context_data(self, **kwargs):  # noqa: ANN003, ANN201
        """Add upload form to context."""
        context = super().get_context_data(**kwargs)
        context["upload_form"] = CSVUploadForm()
        return context


class CSVUploadView(LoginRequiredMixin, FormView):
    """Handle CSV file upload, parse, categorize, and save transactions."""

    form_class = CSVUploadForm
    template_name = "transactions/transaction_list.html"
    success_url = "/transactions/"

    def form_valid(self, form: CSVUploadForm) -> HttpResponse:
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
            categorized = categorize_transactions(self.request.user, parsed_transactions)

            # Get "Unknown" category for uncategorized transactions
            unknown_category, _ = Category.objects.get_or_create(
                user=self.request.user, name="Unknown"
            )

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

    def form_invalid(self, form: CSVUploadForm) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(self.request, "Please select a valid CSV file.")
        return redirect("transactions:list")


class DeleteAllTransactionsView(LoginRequiredMixin, View):
    """Delete all user's transactions for fresh start."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Delete all transactions for current user."""
        count, _ = Transaction.objects.filter(user=request.user).delete()
        messages.success(request, f"Deleted {count} transactions.")
        return redirect("transactions:list")
