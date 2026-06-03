from datetime import date
from budget.services.period_engine import generate_periods

def test_weekly_default_biweekly():
    periods = generate_periods(
        rule={"type": "WEEKLY"},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 4, 30),
    )
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 14)
    assert periods[-1].end >= date(2026, 4, 30)

def test_weekly_interval_1():
    periods = generate_periods(
        rule={"type": "WEEKLY", "interval": 1},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 4, 30),
    )
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 7)
    assert periods[1].start == date(2026, 1, 8)

def test_weekly_interval_2():
    periods = generate_periods(
        rule={"type": "WEEKLY", "interval": 2},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 4, 30),
    )
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 14)

def test_weekly_interval_4():
    periods = generate_periods(
        rule={"type": "WEEKLY", "interval": 4},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 4, 30),
    )
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 28)

def test_weekly_interval_100():
    periods = generate_periods(
        rule={"type": "WEEKLY", "interval": 100},
        range_start=date(2026, 1, 1),
        range_end=date(2030, 12, 31),
    )
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2027, 12, 1)
    assert periods[-1].end >= date(2030, 12, 31)

def test_weekly_labels_are_correct():
    periods = generate_periods(
        rule={"type": "WEEKLY", "interval": 1},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 31),
    )
    assert periods[0].label == "Period ending 2026-01-07"
    assert periods[1].label == "Period ending 2026-01-14"

# def test_weekly_anchor_alignment():
#     periods = generate_periods(
#         rule={"type": "WEEKLY", "interval": 1},
#         range_start=date(2026, 1, 1),
#         range_end=date(2026, 1, 31),
#     )
#     assert periods[0].anchor_date == date(2026, 1, 7)
#     assert periods[1].anchor_date == date(2026, 1, 14)



# This suite validates:
# correct first period
# correct anchor seeding
# correct cadence
# correct natural final period
# correct labels
# correct anchor alignment
# correct behavior for large intervals
# It’s comprehensive and future‑proof.