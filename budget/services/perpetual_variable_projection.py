from dataclasses import dataclass
from datetime import date
from .fixed_term_projection import (
    add_months,
    nth_weekday_of_month,
    day_of_month,
    specific_date_yearly,
    DueRule,
)

@dataclass
class PerpetualVariableDefinition:
    category: any
    amount: float
    anchor_date: date
    due_rule: DueRule
    frequency: str  # "monthly", "quarterly", "annually", "every_x_months"
    months: int | None = None  # for every_x_months
    projection_end_date: date | None = None
    label: str | None = None
    notes: str | None = None


class PerpetualVariableProjectionEngine:

    def compute_anchor(self, rule: DueRule, base_date: date) -> date:
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

    def within_projection_window(self, defn: PerpetualVariableDefinition, anchor_date: date) -> bool:
        if defn.projection_end_date is None:
            return True
        return anchor_date <= defn.projection_end_date

    def project(self, defn: PerpetualVariableDefinition):
        """
        Returns a list of unsaved Budget model instances.
        The caller is responsible for saving them.
        """
        from budget.models import Budget  # local import to avoid circulars

        rows = []
        current_date = defn.anchor_date

        while True:
            anchor = self.compute_anchor(defn.due_rule, current_date)

            if not self.within_projection_window(defn, anchor):
                break

            rows.append(
                Budget(
                    category=defn.category,
                    date=anchor,
                    amount=defn.amount,
                    budget_type=Budget.BUDGET_TYPE_TRANSIENT,
                    is_active=True,
                    label=defn.label or "",
                    notes=defn.notes or "",
                )
            )

            current_date = self.advance(current_date, defn.frequency, defn.months)

        return rows
