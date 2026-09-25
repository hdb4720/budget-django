# budget/budget/views_manager.py

from urllib.parse import urlencode

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views import View

from budget.models import Budget
from budget.budget.forms import BudgetForm

from budget.models import (
    Account,
    Category,
)

from budget.period.period_selector import get_period_selector
from budget.budget.services.manager_context import get_manager_context
from budget.budget.services.manager_detail_row import get_detail_row
from budget.budget.services.manager_requests import get_manager_requests
from budget.budget.services.sandbox import sandbox


class BudgetManagerView(View):
    template_name = "budget/manager/manager.html"

    def get(self, request):
        manager_requests = get_manager_requests(request)
        respond_to = manager_requests["respond_to"]
        selector = get_period_selector(manager_requests["selected"])
        manager_context = get_manager_context(
            selector,
            manager_requests["sorting"],
            manager_requests["filtering"],
        )
        manager_modal_return = {}
        if respond_to == "details":
            manager_modal_return = get_detail_row(
                respond_to,
                manager_requests["manager_modal"],
                manager_context["manager"],
            )
            manager_details = manager_modal_return["manager_details"]
            if len(manager_details) == 1:
                manager_modal = {
                    **manager_requests["manager_modal"],
                    "manager_budget_id": manager_details[0].budget_id,
                }
                respond_to = "selection"
                manager_requests["respond_to"] = respond_to
                manager_requests["manager_modal"] = manager_modal
                manager_modal_return = get_detail_row(
                    respond_to,
                    manager_modal,
                    manager_context["manager"],
                )
        elif respond_to == "selection":
            manager_modal_return = get_detail_row(
                respond_to,
                manager_requests["manager_modal"],
                manager_context["manager"],
            )

        context = {
            **selector,
            **manager_context,
            **manager_requests,
            **manager_modal_return,
        }
        # breakpoint()
        # # Sandbox
        sandbox(context)

        if respond_to == "display":
            return render(request, "budget/manager/_display.html", context)
        elif respond_to == "selector":
            return render(request, "period/_selector.html", context)
        elif respond_to == "table":
            return render(request, "budget/manager/_table.html", context)
        elif respond_to == "details":
            return render(request, "budget/manager/_details_modal.html", context)
        elif respond_to == "selection":
            return render(request, "budget/manager/_selection_modal.html", context)
        else:
            return render(request, self.template_name, context)

    def post(self, request):
        try:
            manager_budget_id = int(
                request.POST.get("manager_budget_id")
            )
        except (TypeError, ValueError):
            raise Http404("Invalid budget identifier.")

        action = request.POST.get("action")
        if action == "delete":
            if manager_budget_id == 0:
                return HttpResponse(
                    "A phantom budget cannot be deleted.",
                    status=400,
                )
            budget = get_object_or_404(
                Budget,
                id=manager_budget_id,
            )
            deleted_budget_id = budget.id
            budget.delete()
            print(f"Deleted Budget {deleted_budget_id}")

            return self._redirect_to_manager(request)

        if action == "create":
            budget = None
        elif action == "update":
            if manager_budget_id == 0:
                raise Http404(
                    "A phantom budget cannot be updated."
                )
            budget = get_object_or_404(
                Budget,
                id=manager_budget_id,
            )
        else:
            return HttpResponse(
                "Invalid budget action.",
                status=400,
            )

        budget_form = BudgetForm(
            request.POST,
            instance=budget,
        )

        if not budget_form.is_valid():
            print("=" * 50)
            print("Budget form is invalid")
            print(budget_form.errors)

            try:
                manager_period_id = int(
                    request.POST.get("manager_period_id")
                )
                manager_category_id = int(
                    request.POST.get("manager_category_id")
                )
            except (TypeError, ValueError):
                raise Http404("Invalid manager row identifiers.")

            category = get_object_or_404(
                Category,
                id=manager_category_id,
            )

            context = {
                "budget_form": budget_form,
                "manager_selection": {
                    "budget_id": manager_budget_id,
                    "category": category.full_path,
                },
                "manager_row": {
                    "period_id": manager_period_id,
                    "category_id": manager_category_id,
                },
                "scheme": {
                    "id": request.POST.get("scheme", ""),
                },
                "period": {
                    "id": request.POST.get("period", ""),
                },
                "selected_date": parse_date(
                    request.POST.get("selected_date", "")
                ),
            }

            return render(
                request,
                "budget/manager/_selection_modal.html",
                context,
                status=200,
            )

        saved_budget = budget_form.save()

        print("=" * 50)
        print(
            f"Saved Budget {saved_budget.id}: "
            f"{saved_budget.category.full_path}, "
            f"{saved_budget.type}, "
            f"{saved_budget.amount}, "
            f"{saved_budget.due_date}"
        )

        return self._redirect_to_manager(request)

    def _redirect_to_manager(self, request):
        query_string = urlencode({
            "scheme": request.POST.get("scheme", ""),
            "period": request.POST.get("period", ""),
            "selected_date": request.POST.get(
                "selected_date",
                "",
            ),
        })

        response = HttpResponse(status=200)

        response["HX-Redirect"] = (
            f"{reverse('budget-manager')}?{query_string}"
        )

        return response
    
    

