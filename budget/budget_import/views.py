from django.shortcuts import render
from django.http import JsonResponse

from budget.budget_import.forms import TransactionImportForm
from budget.budget_import.layouts import LAYOUTS
from budget.budget_import.parser.excel_parser import parse_excel
from budget.budget_import.transform.import_engine import run_import


def transaction_import_view(request):
    if request.method == "POST":
        form = TransactionImportForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data["file"]
            layout_key = form.cleaned_data["layout"]
            dry_run = form.cleaned_data.get("dry_run", False)
            display_results = form.cleaned_data.get("display_results", False)

            # 1. Select layout
            layout = LAYOUTS[layout_key]["layout"]

            # 2. Parse Excel using the shared parser
            df_rows, df_start, df_end = parse_excel(file, layout)

            # 3. Run reconciliation using the shared import engine
            result = run_import(
                df_rows=df_rows,
                df_start=df_start,
                df_end=df_end,
                dry_run=dry_run,
                display_results=display_results,
            )

            # 4. Render results
            return render(
                request,
                "budget_import/import_results.html",
                {"result": result, "title": "Import Results"},
            )

    else:
        form = TransactionImportForm()

    return render(
        request,
        "budget_import/import_form.html",
        {"form": form, "title": "Import Transactions"},
    )
