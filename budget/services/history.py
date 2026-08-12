from django.db.models import Sum
from budget.models import (
    Transaction,
    Period,
)

def planned_history(category, period_end):
    txns = Transaction.objects.filter(
        category=category,
        trn_date__lte=period_end
    ).order_by("trn_date")

    amounts = [t.amount for t in txns]

    if not amounts:
        return {
            "avg": 0,
            "min": 0,
            "max": 0,
            "last": None,
        }

    return {
        "avg": sum(amounts) / len(amounts),
        "min": min(amounts),
        "max": max(amounts),
        "last": txns.last(),
    }

def transient_history(category, scheme, period_end):
    past_periods = Period.objects.filter(
        scheme=scheme,
        end__lte=period_end
    ).order_by("end")

    period_sums = []

    for p in past_periods:
        total = Transaction.objects.filter(
            category=category,
            trn_date__gte=p.start,
            trn_date__lte=p.end
        ).aggregate(total=Sum("amount"))["total"] or 0

        period_sums.append((p.end, total))

    if not period_sums:
        return {
            "avg": 0,
            "min": 0,
            "max": 0,
            "last": None,
        }

    amounts = [amt for _, amt in period_sums]

    return {
        "avg": sum(amounts) / len(amounts),
        "min": min(amounts),
        "max": max(amounts),
        "last": period_sums[-1],
    }

