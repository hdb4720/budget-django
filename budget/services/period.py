from budget.models import Period

def resolve_period(scheme, current_date):
    return Period.objects.get(
        scheme=scheme,
        start__lte=current_date,
        end__gte=current_date
    )
