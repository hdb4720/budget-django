from django.shortcuts import (
    redirect,
    render, 
    get_object_or_404,
)
from django.views.generic import (
    FormView,
    TemplateView,
)
from django.db.models import (
    Min, 
    Max,
)
from django.utils import (
    timezone,
)

from datetime import datetime

from .models import (
    Category,
    PeriodScheme,
    Period,
    Budget,
)
from .forms import (
    BudgetForm,
    FixedTermForm, 
    PerpetualFixedForm, 
    PerpetualVariableForm, 
    ProjectionSettingsForm,
)

from .services.analysis import analyze_period

class BudgetAnalysisView(TemplateView):
    template_name = "budget/budget_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Load all schemes for the selector
        period_schemes = PeriodScheme.objects.all()
        context["period_schemes"] = period_schemes

        # Browse PeriodScheme table with min/max period dates
        schemes = (
            PeriodScheme.objects
            .annotate(
                first_period=Min("periods__start"),
                last_period=Max("periods__end")
            )
            .order_by("name")
        )
        context["schemes"] = schemes

        # Read user inputs
        scheme_name = self.request.GET.get("scheme")
        date_str = self.request.GET.get("date")

        # Defaults
        if not scheme_name:
            scheme_name = period_schemes.first().name

        if not date_str:
            current_date = timezone.now().date()
        else:
            current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        context["scheme"] = scheme_name
        context["current_date"] = current_date

        # Resolve scheme
        scheme = PeriodScheme.objects.get(name=scheme_name)

        # Resolve period
        period = Period.objects.get(
            scheme=scheme,
            start__lte=current_date,
            end__gte=current_date
        )

        # Run analysis
        rows = analyze_period(scheme, current_date)
        context["rows"] = rows

        return context
