from dataclasses import dataclass
from datetime import date, timedelta
import calendar

# ------------------------------------------------------------
# Date helpers
# ------------------------------------------------------------

def add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date(year, month, day)

def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date | None:
    first = date(year, month, 1)
    first_weekday = first.weekday()
    offset = (weekday - first_weekday + 7) % 7
    first_occurrence = first + timedelta(days=offset)
    nth = first_occurrence + timedelta(days=(n - 1) * 7)
    return nth if nth.month == month else None

def day_of_month(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))

def specific_date_yearly(base: date, target_month: int, target_day: int) -> date:
    year = base.year
    try_date = date(year, target_month, target_day)
    if try_date < base:
        try_date = date(year + 1, target_month, target_day)
    return try_date

# ------------------------------------------------------------
# Dataclasses describing the rule and definition
# ------------------------------------------------------------

@dataclass
class DueRule:
    type: str  # "day_of_month" | "nth_weekday" | "specific_date"
    day: int | None = None
    weekday: int | None = None
    n: int | None = None
    month: int | None = None

@dataclass
class FixedTermDefinition:
    category: any
    amount: float
    start_date: date
    due_rule: DueRule
    frequency: str  # "monthly", "quarterly", "annually", "every_x_months"
    months: int | None = None  # for every_x_months
    num_payments: int | None = None
    end_date: date | None = None
    projection_end_date: date | None = None
    label: str | None = None
    notes: str | None = None

# ------------------------------------------------------------
# Projection Engine
# ------------------------------------------------------------

class FixedTermProjectionEngine:

    def compute_due_date(self, rule: DueRule, base_date: date) -> date:
        if rule.type == "day_of_month":
            return day_of_month(base_date.year, base_date.month, rule.day)

        elif rule.type == "nth_weekday":
            return nth_weekday_of_month(
                base_date.year,
                base_date.month,
                rule.weekday,
                rule.n,
            )

        elif rule.type == "specific_date":
            return specific_date_yearly(
                base_date,
                rule.month,
                rule.day,
            )

        raise ValueError(f"Unknown rule type: {rule.type}")

    def advance(self, base_date: date, frequency: str, months: int | None) -> date:
        if frequency == "monthly":
            return add_months(base_date, 1)
        if frequency == "quarterly":
            return add_months(base_date, 3)
        if frequency == "annually":
            return date(base_date.year + 1, base_date.month, base_date.day)
        if frequency == "every_x_months":
            if months is None:
                raise ValueError("months must be provided for every_x_months")
            return add_months(base_date, months)
        raise ValueError(f"Unknown frequency: {frequency}")

    def term_reached(self, defn: FixedTermDefinition, current_date: date, count: int) -> bool:
        if defn.num_payments is not None:
            return count >= defn.num_payments
        if defn.end_date is not None:
            return current_date > defn.end_date
        raise ValueError("Either num_payments or end_date must be provided")

    def within_projection_window(self, defn: FixedTermDefinition, due_date: date) -> bool:
        if defn.projection_end_date is None:
            return True
        return due_date <= defn.projection_end_date

    def project(self, defn: FixedTermDefinition):
        """
        Returns a list of unsaved Budget model instances.
        The caller is responsible for saving them.
        """
        from budget.models import Budget  # local import to avoid circulars

        payments = []
        current_date = defn.start_date
        count = 0

        while not self.term_reached(defn, current_date, count):
            due_date = self.compute_due_date(defn.due_rule, current_date)

            if self.within_projection_window(defn, due_date):
                payments.append(
                    Budget(
                        category=defn.category,
                        date=due_date,
                        amount=defn.amount,
                        budget_type=Budget.BUDGET_TYPE_PLANNED,
                        is_active=True,
                        label=defn.label or "",
                        notes=defn.notes or "",
                    )
                )

            current_date = self.advance(current_date, defn.frequency, defn.months)
            count += 1

        return payments
