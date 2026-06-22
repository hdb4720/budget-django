from django.apps import AppConfig


class BudgetConfig(AppConfig):
    name = 'budget'


class BudgetImportConfig(AppConfig):
    name = "budget.budget_import"

    def ready(self):
        import budget.budget_import.admin

