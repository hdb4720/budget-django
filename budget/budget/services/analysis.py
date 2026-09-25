from decimal import Decimal

class Totals:
    def __init__(self, planned, actual):
        self.planned = planned
        self.actual = actual
        self.diff = planned - actual


def compute_totals(budgets):
    planned = sum((b.amount for b in budgets), Decimal("0"))
    actual = Decimal("0")  # placeholder until we aggregate transactions

    return Totals(planned, actual)
