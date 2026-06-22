# budget/periods/resolver.py

from datetime import date, timedelta
from .period import Period


class PeriodResolver:

    def __init__(self, scheme):
        self.scheme = scheme
        self._periods = None  # lazy cache

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def resolve_for_date(self, dt: date) -> Period:
        for p in self._get_periods():
            if p.start <= dt <= p.end:
                return p
        raise ValueError("Date not in any period")

    def resolve_for_id(self, period_id: str) -> Period:
        for p in self._get_periods():
            if p.id == period_id:
                return p
        raise ValueError(f"Unknown period id: {period_id}")

    def get_prev(self, period: Period) -> Period | None:
        periods = self._get_periods()
        if period.sequence == 1:
            return None
        return periods[period.sequence - 2]

    def get_next(self, period: Period) -> Period | None:
        periods = self._get_periods()
        if period.sequence == len(periods):
            return None
        return periods[period.sequence]

    def generate_periods(self):
        return self._get_periods()

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    def _get_periods(self):
        if self._periods is None:
            self._periods = self._generate_periods()
        return self._periods

    def _generate_periods(self):
        if self.scheme.type == "monthly":
            return self._generate_monthly()
        if self.scheme.type == "nth_weekday":
            return self._generate_nth_weekday()
        if self.scheme.type == "semimonthly":
            return self._generate_semimonthly()
        if self.scheme.type == "annual":
            return self._generate_annual()
        if self.scheme.type == "custom":
            return self._generate_custom()
        raise ValueError("Unknown scheme type")

    # ---------------------------------------------------------
    # MONTHLY
    # ---------------------------------------------------------

    def _generate_monthly(self):
        periods = []
        cursor = self.scheme.start_date
        seq = 1

        while cursor <= self.scheme.end_date:
            start = cursor.replace(day=1)
            end = self._last_day_of_month(start)
            pid = f"{start.year}-{start.month:02d}"
            label = start.strftime("%B %Y")

            periods.append(Period(
                id=pid,
                start=start,
                end=end,
                label=label,
                sequence=seq,
            ))

            seq += 1
            cursor = (end + timedelta(days=1))

        return periods

    @staticmethod
    def _last_day_of_month(dt):
        next_month = dt.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
