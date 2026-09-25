from django.urls import path

from budget.importer.views_importer import transaction_import_view

urlpatterns = [
    path("import-transactions/", transaction_import_view, name="transaction_import"),
]


