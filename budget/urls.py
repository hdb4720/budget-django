from django.urls import path

# Import your budget creation views from wherever they actually live
# from budget.view import (
    # BudgetTypeView,
    # FixedTermFormView,
    # PerpetualFixedFormView,
    # PerpetualVariableFormView,
    # ProjectionSettingsView,
    # BudgetPreviewView,
    # BudgetSaveView,
# )

from .views.dashboard import dashboard

urlpatterns = [
    # path("create/type/", views.BudgetTypeView.as_view(), name="budget_create_type"),
    # path("create/fixed-term/", views.FixedTermFormView.as_view(), name="budget_create_fixed_term"),
    # path("create/perpetual-fixed/", views.PerpetualFixedFormView.as_view(), name="budget_create_perpetual_fixed"),
    # path("create/perpetual-variable/", views.PerpetualVariableFormView.as_view(), name="budget_create_perpetual_variable"),
    # path("create/projection/", views.ProjectionSettingsView.as_view(), name="budget_create_projection"),
    # path("create/preview/", views.BudgetPreviewView.as_view(), name="budget_create_preview"),
    # path("create/save/", views.BudgetSaveView.as_view(), name="budget_create_save"),
    path("dashboard/", dashboard, name="dashboard"),
]
