from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List, Optional, Dict, Any, Tuple

ANCHOR_RULES = {
    "MONTHLY",
    "NTH_WEEKDAY",
    "WEEKLY",
}

BOUNDARY_RULES = {
    "SEMIMONTHLY",
    "USER_DEFINED",
}

@dataclass(frozen=True)
class Period:
    start: date
    end: date
    label: str


class RuleError(ValueError):
    pass

def month_add(year: int, month: int, delta: int) -> Tuple[int, int]:
    """Add delta months to year/month."""
    m = month - 1 + delta
    y = year + m // 12
    m = m % 12 + 1
    return y, m

def last_day_of_month(y: int, m: int) -> date:
    ny, nm = month_add(y, m, 1)
    first_next = date(ny, nm, 1)
    return first_next - timedelta(days=1)

def _end_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)

def _next_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)

def generate_weekly_anchors(range_start: date, range_end: date, interval: int) -> List[date]:
    """
    Generate anchors for WEEKLY rules.

    - First anchor is the last anchor BEFORE range_start
    - Then anchors every interval*7 days
    - Continue until the natural cycle passes range_end
    """

    if interval < 1:
        raise RuleError("interval must be >= 1 for WEEKLY rules")

    step = timedelta(days=interval * 7)
    anchors: List[date] = []

    # 1. Find the anchor BEFORE range_start
    #    This ensures the first period is not lost.
    current = range_start
    while True:
        prev = current - step
        if prev < range_start:
            break
        current = prev

    # Now current is the earliest anchor >= range_start
    # But we need the anchor BEFORE it:
    first_anchor = current - timedelta(days=1)
    anchors.append(first_anchor)

    # 2. Generate forward anchors
    while True:
        next_anchor = anchors[-1] + step
        anchors.append(next_anchor)
        if next_anchor > range_end:
            break

    return anchors

def generate_monthly_anchors(start: date, end: date, interval: int = 1) -> List[date]:
    """
    Returns a list of month-end anchors covering [start, end], including
    the prior month-end before `start`.

    Example:
        start = 2026-01-01, end = 2026-12-31, interval=3
        → [2025-12-31, 2026-03-31, 2026-06-30, 2026-09-30, 2026-12-31]
    """
    anchors = []

    # 1. Compute prior month end
    prior_y, prior_m = month_add(start.year, start.month, -1)
    prior_end = last_day_of_month(prior_y, prior_m)
    anchors.append(prior_end)

    # 2. Start rolling forward from the prior end
    y, m = prior_y, prior_m

    while True:
        # add interval months
        y, m = month_add(y, m, interval)
        anchor = last_day_of_month(y, m)

        if anchor > end:
            break

        anchors.append(anchor)

    return anchors

def nth_weekday(year: int, month: int, weekday: int, nth: int) -> date | None:
    if not (0 <= weekday <= 6):
        raise RuleError("weekday must be 0..6")
    if not (1 <= nth <= 4):
        raise RuleError("nth must be 1..4")

    d = date(year, month, 1)
    days_to_first = (weekday - d.weekday()) % 7
    first_occurrence = d + timedelta(days=days_to_first)

    nth_date = first_occurrence + timedelta(days=7 * (nth - 1))

    if nth_date.month != month:
        return None

    return nth_date

def generate_nth_weekday_anchors(start: date, end: date, weekday: int, nth: int) -> list[date]:
    anchors = []

    py = start.year
    pm = start.month
    current= nth_weekday(py, pm, weekday, nth)
    
    if start < current: 
        py, pm = month_add(start.year, start.month, -1)
        current= nth_weekday(py, pm, weekday, nth)

    nth_date = current
    while nth_date <= end:
        y, m = current.year, current.month
        nth_date = nth_weekday(y, m, weekday, nth)
        anchors.append(nth_date)
        y, m = month_add(y,m, 1)
        current = date(y, m, 1)
        
    return anchors


def generate_semimonthly_periods(range_start: date, range_end: date, cut_day: int):
    if not (2 <= cut_day <= 30):
        raise RuleError("cut_day must be between 2 and 30")

    periods = []
    current = date(range_start.year, range_start.month, 1)

    while current <= range_end:
        year = current.year
        month = current.month

        # First period: 1 → cut_day
        p1_start = date(year, month, 1)
        p1_end = date(year, month, cut_day)

        # Second period: cut_day+1 → EOM
        p2_start = date(year, month, cut_day + 1)
        p2_end = _end_of_month(year, month)

        # Clip to range
        if p1_end >= range_start and p1_start <= range_end:
            periods.append(
                Period(
                    start=max(p1_start, range_start),
                    end=min(p1_end, range_end),
                    label=f"Period ending {p1_end.isoformat()}",
                )
            )

        if p2_end >= range_start and p2_start <= range_end:
            periods.append(
                Period(
                    start=max(p2_start, range_start),
                    end=min(p2_end, range_end),
                    label=f"Period ending {p2_end.isoformat()}",
                )
            )

        # Move to next month
        current = _next_month(current)

    return periods


def generate_anchors_for_rule(rule, range_start, range_end):
    rtype = rule["type"]

    if rtype == "MONTHLY":
        return generate_monthly_anchors(
          range_start, 
          range_end, 
          rule.get("interval", 1)
        )

    elif rtype == "NTH_WEEKDAY":
        weekday = int(rule["weekday"])
        nth = int(rule["nth"])
        return generate_nth_weekday_anchors(range_start, range_end, weekday, nth)
    
    elif rtype == "WEEKLY":
        interval = int(rule.get("interval", 2))  # default = 2 (biweekly)
        return generate_weekly_anchors(
          range_start, 
          range_end, 
          interval
        )

def build_periods_from_anchors(
    anchors: List[date], 
    range_start: date, 
    range_end: date,
    anchor_is_start,
) -> List[Period]:
  
    """
    Convert a monotonically increasing list of anchors into contiguous periods:
      (prev_anchor+1 .. anchor)
    Returns periods that intersect [range_start, range_end].
    """
    if len(anchors) < 2:
        raise RuleError("Need at least two anchors to build periods")

    periods: List[Period] = []
    for prev, cur in zip(anchors[:-1], anchors[1:]):
        if anchor_is_start:
            p_start = prev
            p_end = cur - timedelta(days=1)
            p_label = f"Period beginning {p_start.isoformat()}"
        else:
            p_start = prev + timedelta(days=1)
            p_end = cur
            p_label = f"Period ending {p_end.isoformat()}"
        if p_end < range_start or p_start > range_end:
            continue
        periods.append(Period(start=p_start, end=p_end, label=p_label))

    return periods


def generate_periods(rule, range_start, range_end):
    rtype = rule["type"]

    if rtype in ANCHOR_RULES:
        anchors = generate_anchors_for_rule(rule, range_start, range_end)
        if len(anchors) < 2:
            raise RuleError("Not enough anchors generated for the given range")

        if rtype == "NTH_WEEKDAY":
            # For NTH_WEEKDAY, the anchor is the end of the period, so we set anchor_is_start=False
            anchor_is_start=True
        else:
            anchor_is_start=False
          
        return build_periods_from_anchors(anchors, range_start, range_end, anchor_is_start)

    elif rtype == "SEMIMONTHLY":
        cut_day = int(rule["cut_day"])
        return generate_semimonthly_periods(range_start, range_end, cut_day)

    else:
        raise RuleError(f"Unsupported rule type: {rtype}")


# ============================
# Django Integration Layer
# ============================
try:
    from django.db import transaction
    # from ..models import Period as DjangoPeriod, PeriodScheme
    # Period = DjangoPeriod  # override the dataclass with the Django model
except Exception:
    # Django not available (pure Python or pytest)
    PeriodScheme = None

    # No-op decorator that supports both @atomic and @atomic()
    def atomic_noop(func=None, *args, **kwargs):
        if func is not None:
            return func
        else:
            def decorator(f):
                return f
            return decorator

    class DummyTransaction:
        atomic = atomic_noop

    transaction = DummyTransaction()


def generate_periods_for_scheme(scheme):
    periods = generate_periods(
        rule=scheme.get_rules,
        range_start=scheme.start_date,
        range_end=scheme.end_date
    )
    write_periods(scheme, periods)


@transaction.atomic
def write_periods(scheme, periods):
    from ..models import Period as DjangoPeriod

    DjangoPeriod.objects.filter(scheme=scheme).delete()

    objs = []
    for seq, p in enumerate(periods, start=1):
        objs.append(
            DjangoPeriod(
                scheme=scheme,
                start=p.start,
                end=p.end,
                label=p.label,
                sequence=seq,
            )
        )

    DjangoPeriod.objects.bulk_create(objs)
