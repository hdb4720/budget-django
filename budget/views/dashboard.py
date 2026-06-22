# budget/views/dashboard.py

from datetime import date
from django.shortcuts import render
from budget.models import Budget, Transaction, PeriodScheme
from budget.services.period_navigation import PeriodNavigationService
from budget.services.budget_aggregator import BudgetAggregator


def dashboard(request):
    # 1. Determine the scheme (from user selection or default)
    # scheme = request.user.profile.default_scheme  # or however you store it
    
    # TEMPORARY: until user profiles exist
    scheme = PeriodScheme.objects.first()

    # 2. Determine which period the user selected (if any)
    period_id = request.GET.get("period")

    # 3. Use the new navigation service
    nav_service = PeriodNavigationService(scheme)
    nav = nav_service.get_navigation(period_id)

    # Extract the resolved period
    period = nav["current"]

    # 4. Fetch data for the resolved period
    budgets = Budget.objects.for_period(period)
    transactions = Transaction.objects.for_period(period)

    # 5. Aggregate everything
    snapshot = BudgetAggregator(period, budgets, transactions).aggregate()

    # 6. Render the dashboard
    return render(request, "budget/dashboard.html", {
        "scheme": scheme,
        "period": period,
        "prev_period": nav["previous"],
        "next_period": nav["next"],

        # snapshot contents
        "summary": snapshot.summary,
        "planned_rows": snapshot.planned_rows,
        "transient_rows": snapshot.transient_rows,
        "transaction_rows": snapshot.transaction_rows,
        "category_aggregates": snapshot.category_aggregates,
    })
