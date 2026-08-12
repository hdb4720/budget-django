from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

@dataclass
class BudgetContext:
    budget_amount: Decimal
    paid_to_date: Decimal
    due_date: object
    period_start: object
    period_end: object
    budget_type: str
    historical_min: Decimal | None = None
    historical_max: Decimal | None = None
    actual: Decimal | None = None
    budgeted: Decimal | None = None
    
    
class BudgetStatus(Enum):
    NO_ACTIVITY = "no_activity"
    FUTURE = "future"
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIAL = "partial"
    ACTUAL_EXISTS_NO_BUDGET = "actual_exists_no_budget"
    TRANSACTIONAL_ONLY = "transient_only"
    MISSING_DUE_DATE = "missing_due_date"
    DIFF_NOT_ZERO = "diff_not_zero"
    ABOVE_HISTORICAL = "above_historical"
    BELOW_HISTORICAL = "below_historical"
    OVERSPENT = "overspent"
    AT_RISK = "at_risk"
    ON_TRACK = "on_track"

STATUS_UI = {
    BudgetStatus.OVERDUE: ("overdue", "fa-circle-exclamation", "Overdue", "Budget was due in a past period and remains unpaid."),
    BudgetStatus.DUE: ("due", "fa-clock", "Due", "Budget is due this period and not fully paid."),
    BudgetStatus.AT_RISK: ("at-risk", "fa-triangle-exclamation", "At Risk", "Spending is approaching the budget limit."),
    BudgetStatus.PAID: ("paid", "fa-circle-check", "Paid", "Budget fully paid for this period."),
    BudgetStatus.FUTURE: ("future", "fa-calendar-plus", "Future", "Budget is scheduled for a future period."),
    BudgetStatus.PARTIAL: ("partial", "fa-circle-half-stroke", "Partial", "Budget partially paid but not complete."),
    BudgetStatus.NO_ACTIVITY: ("no-activity", "fa-circle-minus", "No Activity", "No budget and no transactions."),
    BudgetStatus.ACTUAL_EXISTS_NO_BUDGET: ("actual-no-budget", "fa-receipt", "Actual Exists", "Transactions exist but no budget was defined."),
    BudgetStatus.TRANSACTIONAL_ONLY: ("transient-only", "fa-basket-shopping", "Transactional Only", "Transient category has spending but no budget entry."),
    BudgetStatus.DIFF_NOT_ZERO: ("diff", "fa-scale-balanced", "Diff ≠ 0", "Paid-to-date does not match the budget amount."),
    BudgetStatus.OVERSPENT: ("overspent", "fa-fire", "Overspent", "Actual spending exceeds the budget."),
    BudgetStatus.ABOVE_HISTORICAL: ("above-historical", "fa-chart-line", "Above Historical", "Spending exceeds historical maximum."),
    BudgetStatus.BELOW_HISTORICAL: ("below-historical", "fa-chart-area", "Below Historical", "Spending is below historical minimum."),
    BudgetStatus.MISSING_DUE_DATE: ("missing-due", "fa-circle-question", "Missing Due Date", "Budget entry exists but no due date was provided."),
}

# STATUS_UI = {
#     BudgetStatus.OVERDUE: ("overdue", "fa-circle-exclamation", "Overdue", "Budget was due in a past period and remains unpaid."),
#     BudgetStatus.DUE: ("due", "fa-clock", "Due", "Budget is due this period and not fully paid."),
#     BudgetStatus.AT_RISK: ("at-risk", "fa-triangle-exclamation", "At Risk", "Spending is approaching the budget limit."),
#     BudgetStatus.PAID: ("paid", "fa-circle-check", "Paid", "Budget fully paid for this period."),
#     BudgetStatus.FUTURE: ("future", "fa-calendar-plus", "Future", "Budget is scheduled for a future period."),
#     BudgetStatus.PARTIAL: ("partial", "fa-circle-half-stroke", "Partial", "Budget partially paid but not complete."),
#     BudgetStatus.NO_ACTIVITY: ("no-activity", "fa-circle-minus", "No Activity", "No budget and no transactions."),
#     BudgetStatus.ACTUAL_EXISTS_NO_BUDGET: ("actual-no-budget", "fa-receipt", "Actual Exists", "Transactions exist but no budget was defined."),
#     BudgetStatus.TRANSACTIONAL_ONLY: ("transient-only", "fa-basket-shopping", "Transactional Only", "Transient category has spending but no budget entry."),
#     BudgetStatus.DIFF_NOT_ZERO: ("diff", "fa-scale-balanced", "Diff ≠ 0", "Paid-to-date does not match the budget amount."),
#     BudgetStatus.OVERSPENT: ("overspent", "fa-fire", "Overspent", "Actual spending exceeds the budget."),
#     BudgetStatus.ABOVE_HISTORICAL: ("above-historical", "fa-chart-line", "Above Historical", "Spending exceeds historical maximum."),
#     BudgetStatus.BELOW_HISTORICAL: ("below-historical", "fa-chart-area", "Below Historical", "Spending is below historical minimum."),
#     BudgetStatus.MISSING_DUE_DATE: ("missing-due", "fa-circle-question", "Missing Due Date", "Budget entry exists but no due date was provided."),
# }

def compute_status(ctx):
    if ctx.budget_amount == 0 and ctx.paid_to_date == 0:
        return BudgetStatus.NO_ACTIVITY

    if ctx.due_date is None:
        return BudgetStatus.MISSING_DUE_DATE

    if ctx.budget_amount == 0 and ctx.paid_to_date > 0:
        return BudgetStatus.ACTUAL_EXISTS_NO_BUDGET

    if ctx.budget_type == "transient" and ctx.budget_amount == 0 and ctx.paid_to_date > 0:
        return BudgetStatus.TRANSACTIONAL_ONLY

    if ctx.due_date > ctx.period_end:
        return BudgetStatus.FUTURE

    if ctx.paid_to_date >= ctx.budget_amount:
        return BudgetStatus.PAID

    if ctx.due_date < ctx.period_start and ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.OVERDUE

    if ctx.period_start <= ctx.due_date <= ctx.period_end and ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.DUE

    if Decimal("0") < ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.PARTIAL

    if ctx.paid_to_date != ctx.budget_amount:
        return BudgetStatus.DIFF_NOT_ZERO

    if ctx.budget_type == "transient":
        if ctx.historical_max and ctx.paid_to_date > ctx.historical_max:
            return BudgetStatus.ABOVE_HISTORICAL
        if ctx.historical_min and ctx.paid_to_date < ctx.historical_min:
            return BudgetStatus.BELOW_HISTORICAL

    if ctx.actual is not None and ctx.budgeted is not None:
        if ctx.actual > ctx.budgeted:
            return BudgetStatus.OVERSPENT
        if ctx.actual >= ctx.budgeted * Decimal("0.8"):
            return BudgetStatus.AT_RISK
        return BudgetStatus.ON_TRACK

    return BudgetStatus.ON_TRACK
