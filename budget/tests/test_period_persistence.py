import pytest
from datetime import date

from budget.models import PeriodScheme, Period
from budget.services.period_persistence import create_periods_for_scheme


@pytest.mark.django_db
def test_create_periods_for_scheme_monthly():
    scheme = PeriodScheme.objects.create(
        name="Monthly Test",
        scheme_type="MONTHLY",
        monthly_interval=1,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    created = create_periods_for_scheme(scheme)

    assert created == 12
    assert Period.objects.filter(scheme=scheme).count() == 12

    first = Period.objects.filter(scheme=scheme).first()
    assert first.start == date(2024, 1, 1)
    assert first.end == date(2024, 1, 31)