from django.urls import path, include

from budget.budget.views_manager import BudgetManagerView

urlpatterns = [
    path("manager/", BudgetManagerView.as_view(), name="budget-manager"),
    path("importer/", include("budget.importer.urls")),
]


