# budget/forms.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date


# ------------------------------------------------------------
# Shared DueRule form (used by all three budget types)
# ------------------------------------------------------------

class DueRuleForm(forms.Form):
    RULE_CHOICES = [
        ("day_of_month", "Day of Month"),
        ("nth_weekday", "Nth Weekday of Month"),
        ("specific_date", "Specific Date Each Year"),
    ]

    type = forms.ChoiceField(choices=RULE_CHOICES)

    # day_of_month
    day = forms.IntegerField(required=False, min_value=1, max_value=31)

    # nth_weekday
    weekday = forms.IntegerField(required=False, min_value=0, max_value=6)
    n = forms.IntegerField(required=False, min_value=1, max_value=5)

    # specific_date
    month = forms.IntegerField(required=False, min_value=1, max_value=12)

    def clean(self):
        cleaned = super().clean()
        rule_type = cleaned.get("type")

        if rule_type == "day_of_month":
            if cleaned.get("day") is None:
                raise ValidationError("Day is required for day_of_month rule.")

        elif rule_type == "nth_weekday":
            if cleaned.get("weekday") is None or cleaned.get("n") is None:
                raise ValidationError("Weekday and N are required for nth_weekday rule.")

        elif rule_type == "specific_date":
            if cleaned.get("month") is None or cleaned.get("day") is None:
                raise ValidationError("Month and Day are required for specific_date rule.")

        return cleaned


class FixedTermForm(forms.Form):
    category = forms.ModelChoiceField(queryset=None)  # set in __init__
    label = forms.CharField(required=False)
    amount = forms.DecimalField(decimal_places=2, max_digits=10)

    start_date = forms.DateField()

    # embed DueRuleForm fields
    due_rule = DueRuleForm(prefix="rule")

    FREQUENCY_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
        ("every_x_months", "Every X Months"),
    ]
    frequency = forms.ChoiceField(choices=FREQUENCY_CHOICES)
    months = forms.IntegerField(required=False, min_value=1, max_value=24)

    # term definition
    num_payments = forms.IntegerField(required=False, min_value=1)
    end_date = forms.DateField(required=False)

    notes = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        Category = kwargs.pop("CategoryModel")
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()

    def clean(self):
        cleaned = super().clean()

        # validate term definition
        if not cleaned.get("num_payments") and not cleaned.get("end_date"):
            raise ValidationError("You must specify either number of payments or an end date.")

        if cleaned.get("frequency") == "every_x_months" and not cleaned.get("months"):
            raise ValidationError("You must specify X months for every_x_months frequency.")

        return cleaned

    def get_due_rule_data(self):
        return self.fields["due_rule"].clean(self.data)


class PerpetualFixedForm(forms.Form):
    category = forms.ModelChoiceField(queryset=None)
    label = forms.CharField(required=False)
    amount = forms.DecimalField(decimal_places=2, max_digits=10)

    start_date = forms.DateField()

    due_rule = DueRuleForm(prefix="rule")

    FREQUENCY_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
        ("every_x_months", "Every X Months"),
    ]
    frequency = forms.ChoiceField(choices=FREQUENCY_CHOICES)
    months = forms.IntegerField(required=False, min_value=1, max_value=24)

    notes = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        Category = kwargs.pop("CategoryModel")
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("frequency") == "every_x_months" and not cleaned.get("months"):
            raise ValidationError("You must specify X months for every_x_months frequency.")

        return cleaned


class PerpetualVariableForm(forms.Form):
    category = forms.ModelChoiceField(queryset=None)
    label = forms.CharField(required=False)
    amount = forms.DecimalField(decimal_places=2, max_digits=10)

    anchor_date = forms.DateField()

    due_rule = DueRuleForm(prefix="rule")

    FREQUENCY_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
        ("every_x_months", "Every X Months"),
    ]
    frequency = forms.ChoiceField(choices=FREQUENCY_CHOICES)
    months = forms.IntegerField(required=False, min_value=1, max_value=24)

    notes = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        Category = kwargs.pop("CategoryModel")
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("frequency") == "every_x_months" and not cleaned.get("months"):
            raise ValidationError("You must specify X months for every_x_months frequency.")

        return cleaned


class ProjectionSettingsForm(forms.Form):
    PROJECTION_CHOICES = [
        (12, "Next 12 months"),
        (24, "Next 24 months"),
        (36, "Next 36 months"),
        (0, "Custom Range"),
    ]

    projection_window = forms.ChoiceField(choices=PROJECTION_CHOICES)
    projection_end_date = forms.DateField(required=False)

    auto_extend = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()

        if cleaned["projection_window"] == "0" and not cleaned.get("projection_end_date"):
            raise ValidationError("You must specify a projection end date for custom range.")

        # convert window to actual end date
        if cleaned["projection_window"] != "0":
            months = int(cleaned["projection_window"])
            today = date.today()
            cleaned["projection_end_date"] = date(today.year + (today.month + months - 1) // 12,
                                                 (today.month + months - 1) % 12 + 1,
                                                 today.day)

        return cleaned


