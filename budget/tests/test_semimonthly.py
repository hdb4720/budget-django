from datetime import date
from budget.services.period_engine import generate_periods


def test_semimonthly_standard_1_15_16_eom():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 15},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 31),
    )

    assert len(periods) == 2

    # Period 1: 1–15
    assert periods[0].start == date(2026, 1, 1)
    assert periods[0].end == date(2026, 1, 15)

    # Period 2: 16–31
    assert periods[1].start == date(2026, 1, 16)
    assert periods[1].end == date(2026, 1, 31)


def test_semimonthly_cut_day_10():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 10},
        range_start=date(2026, 2, 1),
        range_end=date(2026, 2, 28),
    )

    assert len(periods) == 2

    # Period 1: 1–10
    assert periods[0].start == date(2026, 2, 1)
    assert periods[0].end == date(2026, 2, 10)

    # Period 2: 11–28
    assert periods[1].start == date(2026, 2, 11)
    assert periods[1].end == date(2026, 2, 28)


def test_semimonthly_february_non_leap():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 15},
        range_start=date(2027, 2, 1),
        range_end=date(2027, 2, 28),
    )

    assert len(periods) == 2

    assert periods[0].start == date(2027, 2, 1)
    assert periods[0].end == date(2027, 2, 15)

    assert periods[1].start == date(2027, 2, 16)
    assert periods[1].end == date(2027, 2, 28)


def test_semimonthly_february_leap_year():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 15},
        range_start=date(2028, 2, 1),
        range_end=date(2028, 2, 29),
    )

    assert len(periods) == 2

    assert periods[0].start == date(2028, 2, 1)
    assert periods[0].end == date(2028, 2, 15)

    assert periods[1].start == date(2028, 2, 16)
    assert periods[1].end == date(2028, 2, 29)


def test_semimonthly_multi_month_range():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 15},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 3, 31),
    )

    # 2 periods per month × 3 months = 6 periods
    assert len(periods) == 6

    # Spot‑check March
    assert periods[4].start == date(2026, 3, 1)
    assert periods[4].end == date(2026, 3, 15)

    assert periods[5].start == date(2026, 3, 16)
    assert periods[5].end == date(2026, 3, 31)


def test_semimonthly_labels():
    periods = generate_periods(
        rule={"type": "SEMIMONTHLY", "cut_day": 15},
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 31),
    )

    assert periods[0].label == "Period ending 2026-01-15"
    assert periods[1].label == "Period ending 2026-01-31"
