from datetime import date
from budget.services.period_engine import generate_periods


def test_monthly_interval_1_full_year():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 1},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 12, 31),
    )

    # Should produce 12 periods
    assert len(periods) == 12

    # First period
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 31)
    
    # February (non-leap year)
    assert periods[1].start == date(2026, 2, 1)
    assert periods[1].end == date(2026, 2, 28)

    # December
    assert periods[-1].start == date(2026, 12, 1)
    assert periods[-1].end == date(2026, 12, 31)


def test_monthly_interval_1_multi_year():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 1},
        range_start=date(2026, 1, 1),
        range_end=date(2027, 12, 31),
    )

    # Should produce 24 periods
    assert len(periods) == 24

    # Check a mid-range period
    p = periods[14]  # March 2027
    assert p.start == date(2027, 3, 1)
    assert p.end == date(2027, 3, 31)
    

def test_monthly_interval_3_quarterly():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 3},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 12, 31),
    )

    assert len(periods) == 4

    # Q1
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 3, 31)

    # Q4
    assert periods[3].start == date(2026, 10, 1)
    assert periods[3].end == date(2026, 12, 31)


def test_monthly_interval_6_semiannual():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 6},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 12, 31),
    )

    assert len(periods) == 2

    # First half
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 6, 30)

    # Second half
    assert periods[1].start == date(2026, 7, 1)
    assert periods[1].end == date(2026, 12, 31)


def test_monthly_interval_12_annual():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 12},
        range_start=date(2026, 1, 1),
        range_end=date(2027, 12, 31),
    )

    assert len(periods) == 2

    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 12, 31)

    assert periods[1].start == date(2027, 1, 1)
    assert periods[1].end == date(2027, 12, 31)


def test_monthly_interval_24_biennial():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 24},
        range_start=date(2026, 1, 1),
        range_end=date(2027, 12, 31),
    )

    assert len(periods) == 1

    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2027, 12, 31)


def test_monthly_labels_are_correct():
    periods = generate_periods(
        rule={"type": "MONTHLY", "interval": 1},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 3, 31),
    )

    assert periods[0].label == "Period ending 2026-01-31"
    assert periods[1].label == "Period ending 2026-02-28"
    assert periods[2].label == "Period ending 2026-03-31"


