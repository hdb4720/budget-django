from datetime import date
from budget.services.period_engine import generate_periods
from budget.services.period_engine import RuleError
import pytest

def test_first_monday():
    periods = generate_periods(
        rule={"type": "NTH_WEEKDAY", "weekday": 0, "nth": 1},  # 0 = Monday
        range_start=date(2026, 1, 1),
        range_end=date(2026, 3, 31),
    )

    # 1st Period 12/1/2025 - 1/4/26
    # 2nd Period 1/5/2026 - 2/1/2026
    # 3rd Period 2/2/2026 - 3/1/2026
    # 4th Period 3/2/2026 - 4/5/2026

    assert periods[0].start == date(2025, 12, 1)
    assert periods[0].end == date(2026, 1, 4)
    assert periods[1].start == date(2026, 1, 5)
    assert periods[1].end == date(2026, 2, 1)
    assert periods[2].start == date(2026, 2, 2)
    assert periods[2].end == date(2026, 3, 1)
    assert periods[3].start == date(2026, 3, 2)
    assert periods[3].end == date(2026, 4, 5)


def test_second_friday():
    periods = generate_periods(
        rule={"type": "NTH_WEEKDAY", "weekday": 4, "nth": 2},  # 4 = Friday
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 31),
    )
    
    # Dec 2026 Fridays: 5, 12, 19, 26 → 2nd = Dec 12
    # Jan 2026 Fridays: 2, 9, 16, 23, 30 → 2nd = Jan 9
    assert periods[0].start == date(2025, 12, 12)
    assert periods[0].end == date(2026, 1, 8)


def test_fourth_wednesday():
    periods = generate_periods(
        rule={"type": "NTH_WEEKDAY", "weekday": 2, "nth": 4},  # 2 = Wednesday
        range_start=date(2026, 3, 1),
        range_end=date(2026, 3, 31),
    )

    # Feb 2026 Wednesdays: 4, 11, 18, 25 → 4th = Feb 25
    # Mar 2026 Wednesdays: 4, 11, 18, 25 → 4th = Mar 25
    assert periods[0].start == date(2026, 2, 25)


def test_fifth_monday_exists():
    with pytest.raises(RuleError):
        generate_periods(
            rule={"type": "NTH_WEEKDAY", "weekday": 0, "nth": 5},
            range_start=date(2026, 3, 1),
            range_end=date(2026, 3, 31),
        )

def test_fifth_monday_does_not_exist():
    with pytest.raises(RuleError):
        generate_periods(
            rule={"type": "NTH_WEEKDAY", "weekday": 0, "nth": 5},
            range_start=date(2026, 2, 1),
            range_end=date(2026, 2, 28),
        )


def test_multi_month_range():
    periods = generate_periods(
        rule={"type": "NTH_WEEKDAY", "weekday": 1, "nth": 3},  # 3rd Tuesday
        range_start=date(2026, 1, 1),
        range_end=date(2026, 3, 31),
    )

    # Dec 2026 Tuesdays: 2, 9, 16, 23, 30 → 3rd = Dec 16
    # Jan 2026 Tuesdays: 6, 13, 20, 27 → 3rd = Jan 20
    # Feb 2026 Tuesdays: 3, 10, 17, 24 → 3rd = Feb 17
    # Mar 2026 Tuesdays: 3, 10, 17, 24, 31 → 3rd = Mar 17
    assert periods[0].start == date(2025, 12, 16)
    assert periods[1].start == date(2026, 1, 20)
    assert periods[2].start == date(2026, 2, 17)


def test_labels_are_correct():
    periods = generate_periods(
        rule={"type": "NTH_WEEKDAY", "weekday": 4, "nth": 1},  # 1st Friday
        range_start=date(2026, 1, 1),
        range_end=date(2026, 1, 31),
    )

    assert periods[0].label == "Period beginning 2025-12-05"

