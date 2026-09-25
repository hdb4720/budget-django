from django import forms

from budget.models import Account, Budget, Category


class Html5DateInput(forms.DateInput):
    input_type = "date"


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget

        fields = [
            "category",
            "type",
            "account",
            "amount",
            "due_date",
            "notes",
        ]

        widgets = {
            "category": forms.Select(
                attrs={"class": "form-select"}
            ),
            "type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "account": forms.Select(
                attrs={"class": "form-select"}
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "due_date": Html5DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = (
            Category.objects.order_by("full_path")
        )

        self.fields["account"].queryset = (
            Account.objects.order_by("short_name")
        )

        self.fields["account"].empty_label = "No account"



