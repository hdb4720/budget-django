from django.urls import path, include

from . import view

urlpatterns = [
    path("budget-dashboard/", view.BudgetAnalysisView.as_view(), name="budget_dashboard"),
    path("importer/", include("budget.importer.urls")),
]


