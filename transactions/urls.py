"""URL configuration for transactions app."""

from django.urls import path

from .views import CSVUploadView, DeleteAllTransactionsView, TransactionListView

app_name = "transactions"

urlpatterns = [
    path("", TransactionListView.as_view(), name="list"),
    path("upload/", CSVUploadView.as_view(), name="upload"),
    path("delete-all/", DeleteAllTransactionsView.as_view(), name="delete_all"),
]
