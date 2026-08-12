from dataclasses import dataclass

from django.db.models import Sum

from budget.models import (
    Budget,
    Transaction,
)

from .history import planned_history, transient_history
from .period import resolve_period
from .status import (
    BudgetContext,
    STATUS_UI,
    compute_status,
)

@dataclass
class AnalysisRow:
    category: object
    type: str
    account: object
    budget_amount: float
    due_date: object
    actual: float
    historical_avg: float
    historical_min: float
    historical_max: float
    historical_last: object
    status: object
    status_css: str
    status_icon: str
    status_label: str
    status_tooltip: str


def analyze_period(scheme, current_date):
    period = resolve_period(scheme, current_date)
    budgets = get_budgets_for_period(period)

    rows = []

    for b in budgets:
        # Paid-to-date
        paid = Transaction.objects.filter(
            category=b.category,
            trn_date__gte=period.start,
            trn_date__lte=period.end
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Historical
        if b.type == "planned":
            hist = planned_history(b.category, period.end)
        else:
            hist = transient_history(b.category, scheme, period.end)

        # Status context
        ctx = BudgetContext(
            budget_amount=b.amount,
            paid_to_date=paid,
            due_date=b.due_date,
            period_start=period.start,
            period_end=period.end,
            budget_type=b.type,
            historical_min=hist["min"],
            historical_max=hist["max"],
            actual=paid,
            budgeted=b.amount,
        )

        status = compute_status(ctx)
        css, icon, label, tooltip = STATUS_UI[status]

        rows.append(AnalysisRow(
            category=b.category,
            type=b.type,
            account=b.account,
            budget_amount=b.amount,
            due_date=b.due_date,
            actual=paid,
            historical_avg=hist["avg"],
            historical_min=hist["min"],
            historical_max=hist["max"],
            historical_last=hist["last"],
            status=status,
            status_css=css,
            status_icon=icon,
            status_label=label,
            status_tooltip=tooltip,
        ))

    return rows



def get_budgets_for_period(period):
    return Budget.objects.filter(
        due_date__gte=period.start,
        due_date__lte=period.end
    ).select_related("category", "account")
