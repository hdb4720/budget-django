# budget/services/period_selector.py

from datetime import datetime
from django.utils import timezone
from budget.models import PeriodScheme, Period

def get_period_selector(selected):
    selected_scheme = selected["selected_scheme"]
    selected_period = selected["selected_period"]
    selected_date = selected["selected_date"]

    schemes = PeriodScheme.objects.all()
    if not selected_scheme:
        scheme = schemes.first()
    else:
        scheme = schemes.get(id=selected_scheme)
        
    periods = Period.objects.filter(
        scheme_id=scheme.id
        ).order_by("start")
    
    if not selected_period:
        if not selected_date:
            selected_date = timezone.now().date()
    else:
        period = periods.get(id=selected_period)
        selected_date = period.end
        
    period = periods.get(
        start__lte=selected_date,
        end__gte=selected_date
    )
    
    period_list = list(periods)
    try:
        index = period_list.index(period)
    except ValueError:
        index = -1

    prev_period = period_list[index - 1] if index > 0 else None
    next_period = period_list[index + 1] if index < len(period_list) - 1 else None
    
    return {
        "schemes": schemes,
        "periods": periods,
        "scheme": scheme,
        "period": period,
        "prev_period": prev_period,
        "next_period": next_period,
        "selected_date": selected_date,
    }
