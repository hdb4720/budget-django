# budget/services/budget_types.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from budget.models import Category  # adjust import if needed


@dataclass
class PlannedBudgetRow:
    category: Category
    due_date: date
    amount: Decimal
    status: str
    actual: Optional[Decimal]
    variance: Decimal


@dataclass
class TransientBudgetRow:
    category: Category
    date: date
    estimate: Decimal
    actual: Decimal
    variance: Decimal


@dataclass
class TransactionRow:
    date: date
    category: Optional[Category]
    description: str
    amount: Decimal
    matched_budget: Optional[str]


@dataclass
class CategoryAggregate:
    category: Category
    planned: Decimal
    transient: Decimal
    actual: Decimal
    budgeted: Decimal
    variance: Decimal


@dataclass
class SummaryTotals:
    total_planned: Decimal
    total_transient: Decimal
    total_actual: Decimal
    total_variance: Decimal


@dataclass
class DashboardSnapshot:
    planned_rows: list[PlannedBudgetRow]
    transient_rows: list[TransientBudgetRow]
    transaction_rows: list[TransactionRow]
    category_aggregates: list[CategoryAggregate]
    summary: SummaryTotals
