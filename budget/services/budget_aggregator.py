# budget/services/budget_aggregator.py

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from collections import defaultdict

from django.db import models

from .budget_types import (
    DashboardSnapshot,
    PlannedBudgetRow,
    TransientBudgetRow,
    TransactionRow,
    CategoryAggregate,
    SummaryTotals,
)


class BudgetAggregator:

    def __init__(self, period, budgets_qs, transactions_qs):
        self.period = period
        self.budgets_qs = budgets_qs
        self.transactions_qs = transactions_qs

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def aggregate(self):
        planned_rows = self._aggregate_planned()
        transient_rows = self._aggregate_transient()
        transaction_rows = self._aggregate_transactions()

        category_data = self._aggregate_categories(
            planned_rows, transient_rows, transaction_rows
        )

        summary = self._aggregate_summary(category_data["raw"])

        return DashboardSnapshot(
            planned_rows=planned_rows,
            transient_rows=transient_rows,
            transaction_rows=transaction_rows,
            category_aggregates=category_data["rolled_up"],
            summary=summary,
        )

    # ---------------------------------------------------------
    # PLANNED BUDGETS
    # ---------------------------------------------------------

    def _aggregate_planned(self):
        rows = []

        for b in self.budgets_qs.filter(type="planned"):
            due_date = b.due_date  # planned budgets use their explicit date

            actual = self._match_transaction(b, due_date)
            variance = b.amount - (actual or Decimal("0"))
            status = self._compute_status(b, due_date, actual)

            rows.append(PlannedBudgetRow(
                category=b.category,
                due_date=due_date,
                amount=b.amount,
                status=status,
                actual=actual,
                variance=variance,
            ))

        return rows

    # ---------------------------------------------------------
    # TRANSIENT BUDGETS
    # ---------------------------------------------------------

    def _aggregate_transient(self):
        rows = []

        qs = self.budgets_qs.filter(type="transient")

        # group by category
        by_cat = defaultdict(lambda: Decimal("0"))

        for b in qs:
            by_cat[b.category] += b.amount

        for category, total in by_cat.items():
            rows.append(TransientBudgetRow(
                category=category,
                due_date=self.period.end,  # display at end of period
                estimate=total,
                actual=self._sum_transactions(category),
                variance=total - self._sum_transactions(category),
            ))

        return rows

    # ---------------------------------------------------------
    # TRANSACTIONS
    # ---------------------------------------------------------

    def _aggregate_transactions(self):
        rows = []

        for t in self.transactions_qs:
            matched = self._find_matching_budget(t)

            rows.append(TransactionRow(
                due_date=t.trn_date,
                category=t.category,
                description=t.description,
                amount=t.amount,
                matched_budget=matched,
            ))

        return rows

    # ---------------------------------------------------------
    # CATEGORY AGGREGATES
    # ---------------------------------------------------------

    def _aggregate_categories(self, planned, transient, transactions):
        agg = defaultdict(lambda: CategoryAggregate(
            category=None,
            planned=Decimal("0"),
            transient=Decimal("0"),
            actual=Decimal("0"),
            budgeted=Decimal("0"),
            variance=Decimal("0"),
        ))

        # 1. Leaf-level aggregation
        for row in planned:
            ca = agg[row.category]
            ca.category = row.category
            ca.planned += row.amount

        for row in transient:
            ca = agg[row.category]
            ca.category = row.category
            ca.transient += row.estimate

        for row in transactions:
            if row.category:
                ca = agg[row.category]
                ca.category = row.category
                ca.actual += row.amount

        # Save raw (leaf-level) aggregates BEFORE parent rollups
        raw_aggregates = list(agg.values())

        # Parent rollups
        for ca in raw_aggregates:
            cat = ca.category
            parent = cat.parent
            while parent:
                parent_ca = agg[parent]
                parent_ca.category = parent
                parent_ca.planned += ca.planned
                parent_ca.transient += ca.transient
                parent_ca.actual += ca.actual
                parent = parent.parent

        # Compute budgeted + variance
        for ca in agg.values():
            ca.budgeted = ca.planned + ca.transient
            ca.variance = ca.budgeted - ca.actual

        for ca in agg.values():
            ca.budgeted = ca.planned + ca.transient
            ca.variance = ca.budgeted - ca.actual

            if ca.budgeted == 0 and ca.actual == 0:
                ca.status = "no_activity"
            elif ca.actual > ca.budgeted:
                ca.status = "overspent"
            elif ca.actual >= ca.budgeted * Decimal("0.8"):
                ca.status = "at_risk"
            else:
                ca.status = "on_track"

        # Return both raw and rolled-up aggregates
        return {
            "raw": raw_aggregates,
            "rolled_up": sorted(agg.values(), key=lambda ca: ca.category.full_path),
        }
        # ---------------------------------------------------------
        # SUMMARY TOTALS
        # ---------------------------------------------------------

    def _aggregate_summary(self, raw):
        total_planned = sum(ca.planned for ca in raw)
        total_transient = sum(ca.transient for ca in raw)
        total_actual = sum(ca.actual for ca in raw)
        total_variance = total_planned + total_transient - total_actual

        return SummaryTotals(
            total_planned=total_planned,
            total_transient=total_transient,
            total_actual=total_actual,
            total_variance=total_variance,
        )


    def _match_transaction(self, budget, due_date):
        """
        For planned budgets: find the transaction that satisfies this obligation.
        Matching rule: same category, transaction date within the period.
        """
        tx = self.transactions_qs.filter(
            category=budget.category,
            due_date__gte=self.period.start,
            due_date__lte=self.period.end,
        ).order_by('due_date').first()

        return tx.amount if tx else None

    def _compute_status(self, budget, due_date, actual):
        today = date.today()

        if actual:
            return "paid"

        if due_date < today:
            return "overdue"

        if due_date == today:
            return "due"

        return "upcoming"

    def _sum_transactions(self, category):
        tx = self.transactions_qs.filter(
            category=category,
            trn_date__gte=self.period.start,
            trn_date__lte=self.period.end,
        ).aggregate(total=models.Sum('amount'))

        return tx['total'] or Decimal("0")


    def _find_matching_budget(self, tx):
        """
        Find the budget entry that corresponds to this transaction.
        Only applies to planned budgets.
        """
        return self.budgets_qs.filter(
            type="planned",
            category=tx.category,
            due_date__gte=self.period.start,
            due_date__lte=self.period.end,
        ).order_by('due_date').first()

