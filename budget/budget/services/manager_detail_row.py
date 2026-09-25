# budget/budget/manager_detail_row.py

from django.http import Http404
from django.shortcuts import get_object_or_404

from budget.budget.forms import BudgetForm
from budget.models import Budget

def get_detail_row(respond_to, manager_modal, manager):
    try:
        manager_period_id = int(manager_modal["manager_period_id"])
        manager_category_id = int(manager_modal["manager_category_id"])
    except (TypeError, ValueError, KeyError):
        raise Http404("Invalid manager row identifiers.")

    manager_row = next(
        (
            row
            for row in manager
            if (
                row.period_id == manager_period_id
                and row.category_id == manager_category_id
            )
        ),
        None,
    )

    if manager_row is None:
        raise Http404("Manager row not found.")

    manager_details = manager_row.details
    manager_selection = None
    budget_form = None

    if respond_to == "selection":
        try:
            manager_budget_id = int(
                manager_modal["manager_budget_id"]
            )
        except (TypeError, ValueError, KeyError):
            raise Http404("Invalid budget identifier.")

        manager_selection = next(
            (
                detail
                for detail in manager_details
                if detail.budget_id == manager_budget_id
            ),
            None,
        )

        if manager_selection is None:
            raise Http404("Budget detail not found.")

        if manager_budget_id == 0:
            budget_form = BudgetForm(
                initial={
                    "category": manager_selection.category_id,
                    "type": Budget.BudgetType.TRANSIENT,
                    "due_date": manager_selection.due_date,
                    "amount": manager_selection.amount,
                    "account": manager_selection.account_id,
                    "notes": manager_selection.notes,
                }
            )
        else:
            budget = get_object_or_404(
                Budget,
                id=manager_budget_id,
            )

            budget_form = BudgetForm(
                instance=budget,
            )

    return {
        "manager_row": manager_row,
        "manager_details": manager_details,
        "manager_selection": manager_selection,
        "budget_form": budget_form,
    }


