from django.shortcuts import render

from budget.budget_import.models import ImportLog


def import_history(request):
    logs = ImportLog.objects.order_by("-started_at")[:50]
    return render(
        request,
        "budget_import/import_history.html",
        {"logs": logs},
    )
