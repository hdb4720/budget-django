from django import forms
from budget.importer.layouts import LAYOUTS

class TransactionImportForm(forms.Form):
    file = forms.FileField(label="Select Excel File")

    layout = forms.ChoiceField(
        label="Report Format",
        choices=[(key, value["label"]) for key, value in LAYOUTS.items()],
        initial="quicken",
    )

    dry_run = forms.BooleanField(
        required=False,
        initial=False,
        label="Dry Run (no database changes)"
    )

    display_results = forms.BooleanField(
        required=False,
        initial=True,
        label="Display Results (show inserts/deletes)"
    )
