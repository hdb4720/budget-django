from enum import Enum
from dataclasses import dataclass
from decimal import Decimal


class BudgetStatus(Enum):
    NO_ACTIVITY = "no_activity"
    FUTURE = "future"
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIAL = "partial"
    ACTUAL_EXISTS_NO_BUDGET = "actual_exists_no_budget"
    TRANSACTIONAL_ONLY = "transactional_only"
    MISSING_DUE_DATE = "missing_due_date"
    DIFF_NOT_ZERO = "diff_not_zero"
    ABOVE_HISTORICAL = "above_historical"
    BELOW_HISTORICAL = "below_historical"
    OVERSPENT = "overspent"
    AT_RISK = "at_risk"
    ON_TRACK = "on_track"


@dataclass
class BudgetContext:
    """All inputs needed to compute status for a single budget row."""
    budget_amount: Decimal
    paid_to_date: Decimal
    due_date: object  # datetime.date or None
    period_start: object  # datetime.date
    period_end: object  # datetime.date
    budget_type: str  # "planned" or "transient"
    historical_min: Decimal | None = None
    historical_max: Decimal | None = None
    actual: Decimal | None = None
    budgeted: Decimal | None = None


def compute_budget_status(ctx: BudgetContext) -> BudgetStatus:
    """
    Compute the status for a single budget row using deterministic priority rules.
    """

    # --- 1. No Activity ---
    if ctx.budget_amount == 0 and ctx.paid_to_date == 0:
        return BudgetStatus.NO_ACTIVITY

    # --- 2. Missing Due Date ---
    if ctx.due_date is None:
        return BudgetStatus.MISSING_DUE_DATE

    # --- 3. Actual Exists but No Budget ---
    if ctx.budget_amount == 0 and ctx.paid_to_date > 0:
        return BudgetStatus.ACTUAL_EXISTS_NO_BUDGET

    # --- 4. Transactional Only (Transient special case) ---
    if ctx.budget_type == "transient" and ctx.budget_amount == 0 and ctx.paid_to_date > 0:
        return BudgetStatus.TRANSACTIONAL_ONLY

    # --- 5. Future ---
    if ctx.due_date > ctx.period_end:
        return BudgetStatus.FUTURE

    # --- 6. Paid ---
    if ctx.paid_to_date >= ctx.budget_amount:
        return BudgetStatus.PAID

    # --- 7. Overdue ---
    if ctx.due_date < ctx.period_start and ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.OVERDUE

    # --- 8. Due ---
    if ctx.period_start <= ctx.due_date <= ctx.period_end and ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.DUE

    # --- 9. Partial ---
    if Decimal("0") < ctx.paid_to_date < ctx.budget_amount:
        return BudgetStatus.PARTIAL

    # --- 10. Diff ≠ 0 ---
    if ctx.paid_to_date != ctx.budget_amount:
        return BudgetStatus.DIFF_NOT_ZERO

    # --- 11. Historical Deviation (Transient only) ---
    if ctx.budget_type == "transient":
        if ctx.historical_max is not None and ctx.paid_to_date > ctx.historical_max:
            return BudgetStatus.ABOVE_HISTORICAL
        if ctx.historical_min is not None and ctx.paid_to_date < ctx.historical_min:
            return BudgetStatus.BELOW_HISTORICAL

    # --- 12. Overspent / At Risk / On Track ---
    if ctx.actual is not None and ctx.budgeted is not None:
        if ctx.actual > ctx.budgeted:
            return BudgetStatus.OVERSPENT
        if ctx.actual >= ctx.budgeted * Decimal("0.8"):
            return BudgetStatus.AT_RISK
        return BudgetStatus.ON_TRACK

    # Fallback (should never happen)
    return BudgetStatus.ON_TRACK
