# to run manually
# python manage.py shell < budget/recurrence_test_harness.py
#

from django.test import TestCase

# Create your tests here.

from budget.models import BudgetRecurrence
from datetime import date

def test(rule):
    print("Testing:", rule)
    dates = rule.generate_dates(max_dates=12)
    for d in dates:
        print(" →", d)
    print()

# Daily
rule = BudgetRecurrence(
    frequency="DAILY",
    interval=1,
    start_date=date(2026, 8, 1),
    count=5,
    metadata={}
)

test(rule)

# Weekly
rule = BudgetRecurrence(
    frequency="WEEKLY",
    interval=1,
    anchor_weekday=6,  # Saturday
    start_date=date(2026, 8, 1),
    count=5,
    metadata={}
)

test(rule)

# Monthly - anchor_day
rule = BudgetRecurrence(
    frequency="MONTHLY",
    interval=1,
    anchor_day=31,
    start_date=date(2026, 1, 31),
    count=5,
    metadata={}
)

test(rule)

# Monthly - weekday + ordinal
rule = BudgetRecurrence(
    frequency="MONTHLY",
    interval=1,
    anchor_weekday=2,  # Wednesday
    ordinal=3,         # 3rd
    start_date=date(2026, 8, 1),
    count=5,
    metadata={}
)

test(rule)

# Quarterly
rule = BudgetRecurrence(
    frequency="QUARTERLY",
    interval=1,
    anchor_day=1,
    start_date=date(2026, 7, 1),
    count=4,
    metadata={}
)

test(rule)

# Yearly
rule = BudgetRecurrence(
    frequency="YEARLY",
    interval=1,
    anchor_month=6,
    anchor_day=6,
    start_date=date(2026, 6, 6),
    count=4,
    metadata={}
)

test(rule)

# skip weekends
rule = BudgetRecurrence(
    frequency="MONTHLY",
    interval=1,
    anchor_day=31,
    start_date=date(2026, 1, 31),
    count=3,
    metadata={"skip_weekends": True}
)

test(rule)

# business_day_convention = FOLLOWING
rule = BudgetRecurrence(
    frequency="MONTHLY",
    interval=1,
    anchor_day=31,
    start_date=date(2026, 1, 31),
    count=3,
    metadata={"business_day_convention": "FOLLOWING"}
)

test(rule)

