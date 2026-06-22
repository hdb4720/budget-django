from budget.services.period_engine import generate_periods
from budget.models import Period


def create_periods_for_scheme(scheme) -> int:
    rules = scheme.get_rules()

    spans = generate_periods(
        rule=rules,
        range_start=scheme.start_date,
        range_end=scheme.end_date,
    )

    periods = [
        Period(
            scheme=scheme,
            sequence=i,
            start=span.start,
            end=span.end,
            label=span.label,
        )
        for i, span in enumerate(spans)
    ]

    Period.objects.bulk_create(periods)
    return len(periods)