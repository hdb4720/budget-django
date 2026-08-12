from django.urls import path

from .admin_views import importer_admin_view
from .views import transaction_import_view

urlpatterns = [
    path("import-transactions/", transaction_import_view, name="transaction_import"),
]


