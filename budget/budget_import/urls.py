from django.urls import path

from budget.budget_import.views_dashboard import import_history

from .views import transaction_import_view

from budget.budget_import.views_dashboard import import_history

urlpatterns = [
    path("import-transactions/", transaction_import_view, name="transaction_import"),
    path("import-history/", import_history, name="import_history"),
]



