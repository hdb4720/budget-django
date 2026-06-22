from django.shortcuts import redirect

from django.views.generic import FormView
from django.views.generic import TemplateView

from .forms import (
    FixedTermForm, 
    PerpetualFixedForm, 
    PerpetualVariableForm, 
    ProjectionSettingsForm
)


class BudgetTypeView(TemplateView):
    template_name = "budget/create/type.html"


class FixedTermFormView(FormView):
    template_name = "budget/create/fixed_term.html"
    form_class = FixedTermForm

    def form_valid(self, form):
        self.request.session["budget_form_data"] = form.cleaned_data
        self.request.session["budget_type"] = "fixed_term"
        return redirect("budget_create_projection")


class PerpetualFixedFormView(FormView):
    template_name = "budget/create/perpetual_fixed.html"
    form_class = PerpetualFixedForm

    def form_valid(self, form):
        self.request.session["budget_form_data"] = form.cleaned_data
        self.request.session["budget_type"] = "perpetual_fixed"
        return redirect("budget_create_projection")


class PerpetualVariableFormView(FormView):
    template_name = "budget/create/perpetual_variable.html"
    form_class = PerpetualVariableForm

    def form_valid(self, form):
        self.request.session["budget_form_data"] = form.cleaned_data
        self.request.session["budget_type"] = "perpetual_variable"
        return redirect("budget_create_projection")


class ProjectionSettingsView(FormView):
    template_name = "budget/create/projection.html"
    form_class = ProjectionSettingsForm

    def form_valid(self, form):
        self.request.session["projection_settings"] = form.cleaned_data
        return redirect("budget_create_preview")


class BudgetPreviewView(TemplateView):
    template_name = "budget/create/preview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        budget_type = self.request.session["budget_type"]
        form_data = self.request.session["budget_form_data"]
        proj_data = self.request.session["projection_settings"]

        if budget_type == "fixed_term":
            from budget.services.fixed_term_projection import (
                FixedTermDefinition, FixedTermProjectionEngine, DueRule
            )
            defn = FixedTermDefinition(
                category=form_data["category"],
                amount=form_data["amount"],
                start_date=form_data["start_date"],
                due_rule=DueRule(**form_data["due_rule"]),
                frequency=form_data["frequency"],
                num_payments=form_data.get("num_payments"),
                end_date=form_data.get("end_date"),
                projection_end_date=proj_data["projection_end_date"],
                label=form_data.get("label"),
                notes=form_data.get("notes"),
            )
            engine = FixedTermProjectionEngine()

        elif budget_type == "perpetual_fixed":
            from budget.services.perpetual_fixed_projection import (
                PerpetualFixedDefinition, PerpetualFixedProjectionEngine, DueRule
            )
            defn = PerpetualFixedDefinition(
                category=form_data["category"],
                amount=form_data["amount"],
                start_date=form_data["start_date"],
                due_rule=DueRule(**form_data["due_rule"]),
                frequency=form_data["frequency"],
                projection_end_date=proj_data["projection_end_date"],
                label=form_data.get("label"),
                notes=form_data.get("notes"),
            )
            engine = PerpetualFixedProjectionEngine()

        else:
            from budget.services.perpetual_variable_projection import (
                PerpetualVariableDefinition, PerpetualVariableProjectionEngine, DueRule
            )
            defn = PerpetualVariableDefinition(
                category=form_data["category"],
                amount=form_data["amount"],
                anchor_date=form_data["anchor_date"],
                due_rule=DueRule(**form_data["due_rule"]),
                frequency=form_data["frequency"],
                projection_end_date=proj_data["projection_end_date"],
                label=form_data.get("label"),
                notes=form_data.get("notes"),
            )
            engine = PerpetualVariableProjectionEngine()

        rows = engine.project(defn)
        self.request.session["projected_rows"] = [r.__dict__ for r in rows]

        ctx["rows"] = rows
        return ctx


class BudgetSaveView(TemplateView):
    template_name = "budget/create/success.html"

    def post(self, request, *args, **kwargs):
        from budget.models import Budget

        rows = request.session["projected_rows"]

        for r in rows:
            Budget.objects.create(**r)

        return redirect("budget_create_success")


