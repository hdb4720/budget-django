# budget/budget/services/manager_context.py

from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.db.models import (
    Avg, 
    Min, 
    Max, 
    Sum, 
    OuterRef,
    Subquery,
)

from budget.budget.forms import BudgetForm
from budget.models import (
    Account,
    Category,
    Transaction,
    Budget,
    PeriodSummary
)

from budget.budget.services.budget_manager_classes import (
    BudgetManagerDetailRow,
    BudgetManagerRow,
)

from budget.budget.services.manager_presentation import (
    STATUS_PRESENTATION,
)

from budget.budget.services.budget_constants import ZERO

VALUE_KEYS = {
    "category": lambda row: row.category.casefold(),
    "type": lambda row: (row.type or "").casefold(),
    "account": lambda row: (row.account or "").casefold(),
    "due_date": lambda row: row.due_date,
    "amount": lambda row: row.amount,
    "actual": lambda row: row.actual,
    "difference": lambda row: row.difference,
    "status": lambda row: row.sort_order,
}

SORT_RULES = {
    "category": (
        "category",
    ),
    "type": (
        "type",
        "due_date",
        "category",
    ),
    "account": (
        "account",
        "due_date",
        "category",
    ),
    "due_date": (
        "due_date",
        "type",
        "category",
    ),
    "amount": (
        "amount",
        "category",
    ),
    "actual": (
        "actual",
        "category",
    ),
    "difference": (
        "difference",
        "category",
    ),
    "status": (
        "status",
        "due_date",
        "category",
    ),
}

def get_manager_context(selected, sorting, filtering):
    scheme = selected["scheme"]
    period = selected["period"]
    periods = selected["periods"]
    
    accounts = build_accounts()
    categories = build_categories()
    transactions = build_transactions(period.end_date)
    summaries = build_summaries(scheme, transactions)
    histories = build_histories(period, transactions)
    period_histories = build_period_histories(summaries)
    actuals = build_actuals(period,transactions)
    budgets = build_budgets(period, periods)
    phantoms = build_phantoms(budgets,transactions)
    details = build_details(period, budgets, phantoms)
    manager = build_manager(details, period, histories, period_histories, actuals)
    
    filter_options = build_filter_options(manager)
    manager = manager_filter(manager, filtering)
    manager = manager_sort(manager, sorting)
    
    return {
        "selected": selected,
        "sorting": sorting,
        "filtering": filtering,
        "filter_options": filter_options,
        "accounts": accounts,
        "categories": categories,
        "transactions": transactions,
        "summaries": summaries,
        "histories": histories,
        "period_histories": period_histories,
        "actuals": actuals,
        "budgets": budgets,
        "phantoms": phantoms,
        "details": details,
        "manager": manager,
    }

def build_accounts():
    return Account.objects.order_by("short_name")
    
def build_categories():
    return Category.objects.order_by("full_path")
    
def build_transactions(thru_date):
    transactions = Transaction.objects.exclude(
            category__full_path__startswith="["
        ).filter(
        trn_date__lte=thru_date,
    ).select_related("category", "account")

    return transactions

def build_summaries(scheme, transactions):
    summaries = (
        PeriodSummary.objects
        .exclude(full_path__startswith="[")
        .filter(
            scheme_id=scheme.id,
        )
    )
            
    return summaries

def build_histories(period, transactions):
    histories_qs = (
        transactions
        .values(
            "category_id",
            "category__full_path",
        )
        .annotate(
            min_amount=Min("amount"),
            max_amount=Max("amount"),
            avg_amount=Avg("amount"),
            last_date=Max("trn_date"),
        )
        .order_by("category_id")
    )
    
    histories = {
        row["category_id"]: row
        for row in histories_qs
    }
    
    dated_qs = transactions.values(
        "category_id", 
        "trn_date"
    ).annotate (
        amount=Sum("amount")
    ).order_by (
        "category_id",
        "trn_date"
    )

    dated = {}
    for row in dated_qs:
        dated.setdefault(row["category_id"], {})[row["trn_date"]] = row["amount"]

    for key in histories:
        category_id = histories[key]["category_id"]
        last_date = histories[key]["last_date"]
        last_amount = dated[category_id][last_date]
        histories[key]["last_amount"] = last_amount

    return histories

def build_period_histories(summaries):
    period_histories_qs = (
        summaries
        .values(
            "category_id",
            "full_path",
        )
        .annotate(
            min_amount=Min("amount"),
            max_amount=Max("amount"),
            avg_amount=Avg("amount"),
            last_date=Max("period_end"),
        )
        .order_by("category_id")
    )
    
    period_histories = {
        row["category_id"]: row
        for row in period_histories_qs
    }
    
    dated_qs = summaries.values(
        "category_id", 
        "period_end"
    ).annotate (
        amount=Sum("amount")
    ).order_by (
        "category_id",
        "period_end"
    )

    dated = {}
    for row in dated_qs:
        dated.setdefault(row["category_id"], {})[row["period_end"]] = row["amount"]

    for key in period_histories:
        category_id = period_histories[key]["category_id"]
        last_date = period_histories[key]["last_date"]
        last_amount = dated[category_id][last_date]
        period_histories[key]["last_amount"] = last_amount

    return period_histories

def build_actuals(period, transactions):
    actuals = (
        transactions.filter(
            trn_date__gte=period.start_date,
            trn_date__lte=period.end_date,
        )
        .values("category_id")
        .annotate(
            actual = Sum("amount")
        )
    )

    actuals = { 
        row["category_id"]: row["actual"] 
        for row in actuals 
    }

    return actuals

def build_budgets(period, periods):
    today = timezone.localdate()
    
    matching_period = (
        periods.filter(
            start_date__lte=OuterRef("due_date"),
            end_date__gte=OuterRef("due_date"),
        )
        .order_by("start_date")
        .values("id")[:1]
    )    
    
    budgets = Budget.objects.filter(
        due_date__gte=period.start_date,
    )

    if period.end_date < today:
        budgets = budgets.filter(
            due_date__lte=period.end_date,
        )

    return (
        budgets
        .annotate(
            period_id=Subquery(matching_period),
        )
        .select_related("category", "account")
    )
    
    return budgets    

def build_phantoms(budgets, transactions):
    phantoms = Category.objects.exclude(
        id__in=budgets.values("category_id")
    ).filter(
        id__in=transactions.values("category_id")
    )

    return phantoms

def build_details(period, budgets, phantoms):
    details = defaultdict(list)
    for budget in budgets:
        detail = BudgetManagerDetailRow()

        detail.period_id = budget.period_id
        detail.category_id = budget.category.id

        detail.budget_id = budget.id
        detail.account_id = budget.account_id

        detail.type = budget.type
        detail.due_date = budget.due_date
        detail.amount = budget.amount

        detail.notes = budget.notes

        detail.category = budget.category.full_path
        if budget.account_id:
            detail.account = budget.account.short_name

        details[detail.key].append(detail)
    
    for category in phantoms:
        detail = BudgetManagerDetailRow()

        detail.period_id = period.id
        detail.category_id = category.id
        
        detail.budget_id = 0
        detail.account_id = None

        detail.type = "T"
        detail.due_date = None
        detail.amount = ZERO

        detail.category = category.full_path

        details[detail.key].append(detail)
        
    return details

def build_manager(details, period, histories, period_histories, actuals):
    manager = []
    for key, group in details.items():
        period_id, category_id = key

        row = BudgetManagerRow()
        row.period_id = period_id
        row.category_id = category_id
        row.details = group

        assign_analysis(row, period, histories, period_histories, actuals)
        
        manager.append(row)

    return manager    

def assign_analysis(row, period, histories, period_histories, actuals):
    row.category = row.details[0].category

    assign_account(row)
    assign_type(row)
    assign_amount(row)
    assign_due_date(row)
    assign_actual(row, period, actuals)

    assign_history(row, histories, period_histories)
    assign_status(row, period)
    assign_presentation(row)

def assign_account(row):
    if row.budget_count == 1:
        row.account_id = row.details[0].account_id
        row.account = row.details[0].account
    else:
        account_ids = {
            detail.account_id
            for detail in row.details
        }

        if len(account_ids) == 1:
            row.account_id = next(iter(account_ids))
            row.account = row.details[0].account
        else:
            row.account_id = None
            row.account = "Mixed"
        
def assign_type(row):
    if row.budget_count == 1:
        row.type = row.details[0].type
    else:
        types = {
            detail.type
            for detail in row.details
        }

        if len(types) == 1:
            row.type = next(iter(types))
        else:
            row.type = "Mixed"

def assign_amount(row):
    row.amount = sum((detail.amount for detail in row.details),ZERO)

def assign_actual(row, period, actuals):
    if row.period_id == period.id:
        row.actual = actuals.get(row.category_id) or ZERO
        row.difference = max(((row.amount - row.actual) * row.direction), ZERO)
    else:
        row.actual = ZERO
        row.difference = ZERO

def assign_due_date(row):
    sorted_details = sorted(
        row.details,
        key=lambda detail: (detail.due_date, detail.budget_id),
    )

    if not row.is_phantom:
        met = False
        running_amount = ZERO
        row.due_date = None
        for detail in sorted_details:
            running_amount += detail.amount
            if not met:
                row.due_date = detail.due_date
                met = (row.actual or ZERO) * row.direction <= running_amount * row.direction
    
    return row

def assign_status(row, period):
    # Status        Definition
    # ============= ====================================================================================
    # incomplete    The row has an assigned due date but its budget amount is zero.
    # active        The row budget amount is zero, but its actual amount is not zero.   
    # met           Actual equals the nonzero consolidated budget.
    # due_today     The row remains underfilled and its assigned due date is today.
    # overdue       The row remains underfilled and its assigned due date is before today.
    # pending       The row remains underfilled, is not overdue, and has no payment or receipt activity.
    # partial       The row remains underfilled, is not overdue, and has some payment or receipt activity.
    # overfilled    The row is overfilled, more paid then budgetted for
    # other         An unexpected condition not covered by the defined rules; retained as a diagnostic fallback.
    # future        The assigned due date is current period.
    
    as_of_date = timezone.localdate()
    current_position = ((row.amount - row.actual) * row.direction)
    
    if row.is_phantom:
        if row.actual != 0:
            row.status = "Active"
        else:
            row.status = "Unbudgeted"
    elif row.period_id != period.id:
        row.status = "Future"
    else:
        if row.amount == 0:
            if row.actual == 0:
                row.status = "Incomplete"
            else:
                row.status = "Active"
        else:
            if row.type == "P":
                if current_position == 0: # Budget met
                    row.status = "Met"
                elif current_position > 0: # Budget still open
                    if row.due_date == as_of_date: 
                        row.status = "Due Today"
                    elif row.due_date < as_of_date:
                        row.status = "Overdue"
                    elif row.due_date > as_of_date:
                        if row.actual == 0:
                            row.status = "Pending"
                        elif row.actual != 0:
                            row.status = "Partial"
                elif current_position < 0: # Budget exceeded
                    row.status = "Overfilled"
            else:
                if current_position == ZERO:
                    row.status = "Budget Used"
                elif current_position < ZERO:
                    row.status = "Overfilled"
                else:  # Transient budget still has funds available
                    if row.actual == ZERO:
                        row.status = "Available"
                    elif row.due_date <= as_of_date:
                        row.status = "On Track"
                    else:
                        row.status = "Watch"        
    return row

def assign_presentation(row):
    row.css_class = row.status.lower().replace(" ", "-")
    row.icon = STATUS_PRESENTATION.get(row.status, {}).get("icon", "fa-circle-question")
    row.label = STATUS_PRESENTATION.get(row.status, {}).get("label", "Other")
    row.sort_order = STATUS_PRESENTATION.get(row.status, {}).get("sort_order", 999)

def assign_history(row, histories, period_histories):
    if (row.type or "").upper() == "T":
        history = period_histories.get(row.category_id)
    else:
        history = histories.get(row.category_id)

    if history is not None:
        row.min_amount = history["min_amount"]
        row.max_amount = history["max_amount"]
        row.avg_amount = history["avg_amount"]
        row.last_amount = history["last_amount"]
        row.last_date = history["last_date"]
    else:
        row.min_amount = ZERO
        row.max_amount = ZERO
        row.avg_amount = ZERO
        row.last_amount = ZERO
        row.last_date = None

def build_filter_options(manager):
    categories = {}

    for row in manager:
        categories[row.category_id] = row.category

    category_options = [
        {
            "category_id": category_id,
            "category": category,
        }
        for category_id, category in categories.items()
    ]

    category_options.sort(
        key=lambda option: option["category"].casefold()
    )
    
    types = set()
    for row in manager:
        if row.type:
            types.add(row.type)

    type_options = sorted(
        types,
        key=str.casefold,
    )

    statuses = set()
    for row in manager:
        if row.status:
            statuses.add(row.status)

    status_options = sorted(
        statuses,
        key=str.casefold,
    )

    return {
        "categories": category_options,
        "types": type_options,
        "statuses": status_options,
    }
        
def manager_filter(manager, filtering):
    filtered_manager = manager
    
    return filtered_manager

def manager_sort(manager, sorting):
    sort_field = sorting["sort_field"]
    if sort_field not in VALUE_KEYS:
        sort_field = "due_date"
        sorting["sort_field"] = sort_field

        
    sort_direction = sorting["sort_direction"]
    if sort_direction not in ("asc", "desc"):
        sort_direction = "asc"
        sorting["sort_direction"] = sort_direction

    fields = SORT_RULES[sort_field]
    sorted_manager = list(manager)

    # Apply secondary fields from lowest to highest priority.
    for field in reversed(fields[1:]):
        if field != "due_date":
            sorted_manager.sort(
                key=VALUE_KEYS[field]
            )
        else:
            sorted_manager.sort(
                key=lambda item: (
                    item.due_date is None,
                    item.due_date or date.max,
                ),
            )

    # Apply the primary field last, in the requested direction.
    primary_field = fields[0]
    if primary_field != "due_date":
        sorted_manager.sort(
            key=VALUE_KEYS[primary_field],
            reverse=(sort_direction == "desc"),
        )
    else:    
        if sort_direction == "desc":
            sorted_manager.sort(
                key=lambda item: (
                    item.due_date is not None,
                    item.due_date or date.min,
                ),
                reverse=True,
            )
        else:
            sorted_manager.sort(
                key=lambda item: (
                    item.due_date is None,
                    item.due_date or date.max,
                ),
            )    

    return sorted_manager

