import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField  
from django.utils import timezone



###########################################################################
# Helper modules
###########################################################################
class TransactionQuerySet(models.QuerySet):
    def for_period(self, period):
        return self.filter(trn_date__gte=period.start, trn_date__lte=period.end)

class BudgetQuerySet(models.QuerySet):
    def for_period(self, period):
        return self.filter(due_date__gte=period.start, due_date__lte=period.end)

###########################################################################
# Models
###########################################################################

class Account(models.Model):
    name = models.TextField(unique=True)
    short_name = models.CharField(max_length=20, blank=True)
    institution = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=50)
    opening_date = models.DateField(db_column='beginning_date', null=True, blank=True)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name


class Category(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.SET_NULL
    )
    full_path = models.TextField(unique=True)
    level = models.IntegerField(db_column='depth')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_path']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.full_path


class Transaction(models.Model):
    account = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT, 
        related_name='transactions',
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='transactions', 
        null=True, 
        blank=True,
    )
    trn_date = models.DateField()
    description = models.CharField(max_length=200)
    memo = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    seq = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionQuerySet.as_manager()    
    
    
    class Meta:
        ordering = ['-trn_date']

    def __str__(self):
        return f"{self.trn_date} - {self.description} - {self.category} - {self.amount}"

    @property
    def txn_type(self):
        """
        Derived field:
        - NORMAL if category is not an account
        - TRANSFER if category matches an account name or short_name
        """
        from .models import Account
        account_names = list(Account.objects.values_list('name', flat=True))
        short_names = list(Account.objects.values_list('short_name', flat=True))
        if self.category in account_names or self.category in short_names:
            return "TRANSFER"
        return "NORMAL"


class Budget(models.Model):

    class BudgetType(models.TextChoices):
        PLANNED = "planned", "Planned"      # A dated obligation
        TRANSIENT = "transient", "Transient"  # A dated spending intention

    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='budgets', 
    )

    # For PLANNED: the due date of the obligation
    # For TRANSIENT: the anchor date used to assign this budget to a period
    due_date = models.DateField()

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    type = models.CharField(
        max_length=20,
        choices=BudgetType.choices,
    )
    seq = models.IntegerField(default=0)

    # Optional: which account is expected to satisfy this budget
    account = models.ForeignKey(
        Account, 
        on_delete=models.PROTECT, 
        related_name='budgets',
        null=True, 
        blank=True,
    )

    notes = models.TextField(blank=True, null=True) 

    created_at = models.DateTimeField(
        default=timezone.now, 
        editable=False,
        null=False,
        blank=True,
    )
    updated_at = models.DateTimeField(
        default=timezone.now,
        null=False,
        blank=True,
    )

    objects = BudgetQuerySet.as_manager()

    class Meta:
        ordering = ["due_date", "category__full_path"]


class BudgetRecurrence(models.Model):
    FREQUENCY_CHOICES = [
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
        ("QUARTERLY", "Quarterly"),
        ("YEARLY", "Yearly"),
    ]

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval = models.PositiveIntegerField(default=1)

    anchor_day = models.IntegerField(null=True, blank=True)
    anchor_weekday = models.IntegerField(null=True, blank=True)
    ordinal = models.IntegerField(null=True, blank=True)
    anchor_month = models.IntegerField(null=True, blank=True)

    start_date = models.DateField()
    until = models.DateField(null=True, blank=True)
    count = models.PositiveIntegerField(null=True, blank=True)

    timezone = models.CharField(max_length=50, default="UTC")
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.frequency} every {self.interval}"

    def clean(self):
        errors = {}

        # Frequency required
        if not self.frequency:
            errors["frequency"] = "Frequency is required."

        # Interval must be positive
        if self.interval < 1:
            errors["interval"] = "Interval must be >= 1."

        # Start date required
        if not self.start_date:
            errors["start_date"] = "Start date is required."

        # Termination rules
        if self.count is not None and self.count < 1:
            errors["count"] = "Count must be >= 1."

        if self.until and self.start_date and self.until < self.start_date:
            errors["until"] = "Until date must be >= start_date."

        if not self.count and not self.until:
            # Perpetual is allowed — no error
            pass

        # Frequency-specific anchor validation
        freq = self.frequency

        if freq == "DAILY":
            if any([self.anchor_day, self.anchor_weekday, self.ordinal, self.anchor_month]):
                errors["anchors"] = "Daily recurrence cannot use anchors."

        elif freq == "WEEKLY":
            if self.anchor_weekday is None:
                errors["anchor_weekday"] = "Weekly recurrence requires anchor_weekday."
            if any([self.anchor_day, self.ordinal, self.anchor_month]):
                errors["anchors"] = "Weekly recurrence cannot use day or ordinal anchors."

        elif freq == "MONTHLY":
            valid_day_pattern = self.anchor_day is not None and self.anchor_weekday is None and self.ordinal is None
            valid_weekday_pattern = self.anchor_weekday is not None and self.ordinal is not None and self.anchor_day is None

            if not (valid_day_pattern or valid_weekday_pattern):
                errors["anchors"] = "Monthly recurrence requires either anchor_day or (anchor_weekday + ordinal)."

        elif freq == "QUARTERLY":
            if self.anchor_day is None:
                errors["anchor_day"] = "Quarterly recurrence requires anchor_day."
            if any([self.anchor_weekday, self.ordinal, self.anchor_month]):
                errors["anchors"] = "Quarterly recurrence cannot use weekday or month anchors."

        elif freq == "YEARLY":
            if self.anchor_month is None:
                errors["anchor_month"] = "Yearly recurrence requires anchor_month."
            if self.anchor_day is None:
                errors["anchor_day"] = "Yearly recurrence requires anchor_day."
            if any([self.anchor_weekday, self.ordinal]):
                errors["anchors"] = "Yearly recurrence cannot use weekday anchors."

        # Metadata validation
        if self.metadata:
            if not isinstance(self.metadata, dict):
                errors["metadata"] = "Metadata must be a JSON object."

            if "seasonal_months" in self.metadata:
                months = self.metadata["seasonal_months"]
                if not all(1 <= m <= 12 for m in months):
                    errors["metadata"] = "seasonal_months must contain values 1–12."

        if errors:
            raise ValidationError(errors)

    def generate_dates(self, max_dates=None):
        dates = []
        current = self.start_date
        occurrences = 0

        while True:
            if self.count and occurrences >= self.count:
                break

            if self.until and current > self.until:
                break

            if "seasonal_months" in self.metadata:
                if current.month not in self.metadata["seasonal_months"]:
                    current = self.step_forward(current)
                    continue

            current = self.apply_business_day_convention(current)

            if self.metadata.get("skip_weekends"):
                current = self.shift_to_monday_if_weekend(current)

            dates.append(current)
            occurrences += 1

            current = self.step_forward(current)
            current = self.apply_anchor(current)

            if max_dates and len(dates) >= max_dates:
                break

        return dates

    def step_forward(self, current):
        freq = self.frequency
        interval = self.interval or 1

        if freq == "DAILY":
            # Move forward N days
            return current + timedelta(days=interval)

        if freq == "WEEKLY":
            # Move forward N weeks
            return current + timedelta(weeks=interval)

        if freq == "MONTHLY":
            # Move forward N months (same day number, best effort)
            return self._add_months(current, interval)

        if freq == "QUARTERLY":
            # Move forward N * 3 months
            return self._add_months(current, interval * 3)

        if freq == "YEARLY":
            # Move forward N years (same month/day, best effort)
            return self._add_years(current, interval)

        # Fallback: no change
        return current

    def _add_months(self, current, months):
        # naive but effective month addition
        year = current.year
        month = current.month + months
        day = current.day

        # normalize year/month
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1

        # clamp day to last day of target month
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)

        return date(year, month, day)

    def _add_years(self, current, years):
        year = current.year + years
        month = current.month
        day = current.day

        # handle Feb 29 → Feb 28 in non-leap years
        try:
            return date(year, month, day)
        except ValueError:
            if month == 2 and day == 29:
                return date(year, 2, 28)
            raise

    def apply_anchor(self, current):
        freq = self.frequency

        # DAILY and WEEKLY do not use anchors
        if freq in ("DAILY", "WEEKLY"):
            return current

        # MONTHLY: two patterns
        if freq == "MONTHLY":
            # Pattern 1: anchor_day (e.g., 15th of each month)
            if self.anchor_day is not None:
                year = current.year
                month = current.month
                day = min(self.anchor_day, calendar.monthrange(year, month)[1])
                return date(year, month, day)

            # Pattern 2: weekday + ordinal (e.g., 3rd Wednesday)
            if self.anchor_weekday is not None and self.ordinal is not None:
                return self._nth_weekday_of_month(
                    current.year,
                    current.month,
                    self.anchor_weekday,
                    self.ordinal
                )

        # QUARTERLY: anchor_day only
        if freq == "QUARTERLY":
            year = current.year
            month = current.month
            day = min(self.anchor_day, calendar.monthrange(year, month)[1])
            return date(year, month, day)

        # YEARLY: anchor_month + anchor_day
        if freq == "YEARLY":
            year = current.year
            month = self.anchor_month
            day = min(self.anchor_day, calendar.monthrange(year, month)[1])
            return date(year, month, day)

        return current

    def _nth_weekday_of_month(self, year, month, weekday, ordinal):
        # weekday: 0=Monday, ordinal: 1=first, ..., -1=last
        first_day_weekday, days_in_month = calendar.monthrange(year, month)

        # Find the first occurrence of the target weekday
        offset = (weekday - first_day_weekday) % 7
        first_occurrence = 1 + offset

        if ordinal > 0:
            # e.g., 3rd Wednesday
            day = first_occurrence + (ordinal - 1) * 7
            if day > days_in_month:
                day = first_occurrence + (ordinal - 2) * 7
            return date(year, month, day)

        else:
            # ordinal == -1 → last weekday of the month
            last_occurrence = first_occurrence
            while last_occurrence + 7 <= days_in_month:
                last_occurrence += 7
            return date(year, month, last_occurrence)

    def apply_business_day_convention(self, dt):
        convention = self.metadata.get("business_day_convention")

        # No convention → return unchanged
        if not convention:
            return dt

        weekday = dt.weekday()  # 0=Mon, 6=Sun

        # Already a business day
        if weekday < 5:
            return dt

        # FOLLOWING
        if convention == "FOLLOWING":
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
            return dt

        # PRECEDING
        if convention == "PRECEDING":
            while dt.weekday() >= 5:
                dt -= timedelta(days=1)
            return dt

        # MODIFIED FOLLOWING
        if convention == "MODIFIED_FOLLOWING":
            original_month = dt.month
            temp = dt
            while temp.weekday() >= 5:
                temp += timedelta(days=1)
            if temp.month != original_month:
                # fallback to preceding
                temp = dt
                while temp.weekday() >= 5:
                    temp -= timedelta(days=1)
            return temp

        # MODIFIED PRECEDING
        if convention == "MODIFIED_PRECEDING":
            original_month = dt.month
            temp = dt
            while temp.weekday() >= 5:
                temp -= timedelta(days=1)
            if temp.month != original_month:
                # fallback to following
                temp = dt
                while temp.weekday() >= 5:
                    temp += timedelta(days=1)
            return temp

        return dt

    def shift_to_monday_if_weekend(self, dt):
        # 0 = Monday, 6 = Sunday
        weekday = dt.weekday()

        # Saturday → Monday
        if weekday == 5:
            return dt + timedelta(days=2)

        # Sunday → Monday
        if weekday == 6:
            return dt + timedelta(days=1)

        return dt


class BudgetDefinition(models.Model):
    class RecurrenceType(models.TextChoices):
        FIXED_TERM = "FIXED_TERM", "Fixed Term"
        PERPETUAL_FIXED = "PERPETUAL_FIXED", "Perpetual Fixed"
        PERPETUAL_VARIABLE = "PERPETUAL_VARIABLE", "Perpetual Variable"

    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recurrence_type = models.CharField(max_length=20, choices=RecurrenceType.choices)
    recurrence = models.ForeignKey(BudgetRecurrence, on_delete=models.CASCADE)

    def make_planned_row(self, date):
        return Budget(
            category=self.category,
            amount=self.amount,
            due_date=date,
            type="planned",
        )

    def make_transient_row(self, date):
        return Budget(
            category=self.category,
            amount=self.amount,
            due_date=date,
            type="transient",
        )

    def project_budget(self, window_end=None):
        dates = self.recurrence.generate_dates()

        rows = []
        for date in dates:
            if window_end and date > window_end:
                break

            if self.recurrence_type == "FIXED_TERM":
                rows.append(self.make_planned_row(date))

            elif self.recurrence_type == "PERPETUAL_FIXED":
                rows.append(self.make_planned_row(date))

            elif self.recurrence_type == "PERPETUAL_VARIABLE":
                rows.append(self.make_transient_row(date))

        return rows


class PeriodScheme(models.Model):
    """
    PeriodScheme Model
    This model represents a scheme for defining periodic intervals with various types of rules. 
    It supports multiple scheme types such as WEEKLY, MONTHLY, SEMIMONTHLY, and NTH_WEEKDAY, 
    each with its own specific configuration fields.
    Attributes:
        SCHEME_TYPES (list): Choices for the type of period scheme.
        name (CharField): The unique name of the period scheme.
        scheme_type (CharField): The type of the scheme, selected from SCHEME_TYPES.
        start_date (DateField): The optional start date for the scheme.
        end_date (DateField): The optional end date for the scheme.
        weekly_interval (PositiveIntegerField): Interval in weeks for WEEKLY schemes.
        monthly_interval (PositiveIntegerField): Interval in months for MONTHLY schemes.
        cut_day (PositiveSmallIntegerField): Day of the month for SEMIMONTHLY schemes.
        nth_weekday (PositiveSmallIntegerField): Weekday (0=Monday, 6=Sunday) for NTH_WEEKDAY schemes.
        nth_ordinal (PositiveSmallIntegerField): Ordinal (1=first, 2=second, etc.) for NTH_WEEKDAY schemes.
        rules (JSONField): JSON representation of the rules for the scheme.
        notes (TextField): Optional notes about the scheme.
    Methods:
        clean(): Validates the fields based on the selected scheme type.
        get_rules(): Generates a dictionary representation of the rules based on the scheme type.
        save(*args, **kwargs): Overrides the save method to regenerate rules and validate the model.
        __str__(): Returns the name of the scheme as its string representation.
    """

    SCHEME_TYPES = [
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
        ("SEMIMONTHLY", "Semi-Monthly"),
        ("NTH_WEEKDAY", "Nth Weekday"),
    ]

    # Identity
    name = models.CharField(max_length=100, unique=True)

    # Rule selector
    scheme_type = models.CharField(max_length=50, choices=SCHEME_TYPES)

    # Date range
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Rule-specific fields
    # WEEKLY
    weekly_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of weeks between anchors (1 = weekly, 2 = biweekly, etc.)"
    )

    # MONTHLY
    monthly_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of months between periods (1 = monthly, 3 = quarterly, etc.)"
    )
    
    # SEMIMONTHLY
    cut_day = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Day of month where the split occurs (2–30)"
    )

    #NTH_WEEKDAY
    nth_weekday = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="0=Monday, 6=Sunday"
    )

    nth_ordinal = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="1=first, 2=second, 3=third, 4=fourth"
    )

    # JSON fallback for flexible rule storage (optional, can be used for custom schemes)
    rules = models.JSONField()

    # Notes
    notes = models.TextField(blank=True)

    def clean(self):
        if self.scheme_type == "WEEKLY":
            if self.weekly_interval is None:
                raise ValidationError("Weekly interval is required for WEEKLY schemes.")
            if self.weekly_interval < 1:
                raise ValidationError("Weekly interval must be at least 1.")

        elif self.scheme_type == "MONTHLY":
            if self.monthly_interval is None:
                raise ValidationError("monthly_interval is required for MONTHLY schemes.")
            if self.monthly_interval < 1:
                raise ValidationError("monthly_interval must be at least 1.")

        elif self.scheme_type == "SEMIMONTHLY":
            if self.cut_day is None:
                raise ValidationError("cut_day is required for SEMIMONTHLY schemes.")
            if not (2 <= self.cut_day <= 30):
                raise ValidationError("cut_day must be between 2 and 30.")

        elif self.scheme_type == "NTH_WEEKDAY":
            if self.nth_weekday is None:
                raise ValidationError("weekday is required for NTH_WEEKDAY schemes.")
            if not (0 <= self.nth_weekday <= 6):
                raise ValidationError("weekday must be between 0 and 6.")

            if self.nth_ordinal is None:
                raise ValidationError("nth is required for NTH_WEEKDAY schemes.")
            if not (1 <= self.nth_ordinal <= 4):
                raise ValidationError("nth must be between 1 and 4.")

        else:
            raise ValidationError("Scheme type unrecognized")

    def get_rules(self):
        if self.scheme_type == "WEEKLY":
            return {
                "type": "WEEKLY",
                "interval": self.weekly_interval,
            }

        if self.scheme_type == "MONTHLY":
            return {
                "type": "MONTHLY",
                "interval": self.monthly_interval,
            }

        if self.scheme_type == "SEMIMONTHLY":
            return {
                "type": "SEMIMONTHLY",
                "cut_day": self.cut_day,
            }

        if self.scheme_type == "NTH_WEEKDAY":
            return {
                "type": "NTH_WEEKDAY",
                "weekday": self.nth_weekday,
                "nth": self.nth_ordinal,
            }

        return self.rules

    def save(self, *args, **kwargs):
        # Always regenerate the rules dict from structured fields
        self.rules = self.get_rules()

        # Run full validation before saving
        self.full_clean()

        super().save(*args, **kwargs)
                

    def __str__(self):
        return self.name


class Period(models.Model):
    # The scheme this period belongs to
    scheme = models.ForeignKey(
        PeriodScheme,
        on_delete=models.CASCADE,
        related_name='periods'
    )

    # Start and end boundaries of the period
    start = models.DateField()
    end = models.DateField()

    # Human-friendly label (e.g., "2026-04", "Apr 2026", "P12", "4th Wed - Apr")
    label = models.CharField(max_length=100)

    # Sequence number (monotonic increasing index)
    # Example: 1, 2, 3, ... for each scheme
    sequence = models.IntegerField()

    # Optional notes for debugging or UI
    notes = models.TextField(blank=True)

    class Meta:
        # Ensure periods for a scheme are ordered and unique
        ordering = ['scheme', 'sequence']
        unique_together = ('scheme', 'sequence')

    def __str__(self):
        return f"{self.scheme.name}: {self.label}"


class ImporterEntry(models.Model):
    """
    ImporterEntry is a Django model class that represents an entry for running an importer.
    This model is not managed by Django's ORM, meaning it does not create or modify the
    corresponding database table. It is primarily used for interacting with an existing
    database table or for other specific purposes.

    Attributes:
        Meta (class): Contains metadata for the model.
            - managed (bool): Indicates that Django should not manage the database table.
            - verbose_name (str): A human-readable name for the model in singular form.
            - verbose_name_plural (str): A human-readable name for the model in plural form.
    """
    class Meta:
        managed = False
        verbose_name = "Run Importer"
        verbose_name_plural = "Run Importer"


class BudgetDashboardEntry(models.Model):
    """
    BudgetDashboardEntry is a Django model class that represents an entry for the budget dashboard.
    This model is not managed by Django's ORM, meaning it does not create or modify the
    corresponding database table. It is primarily used for interacting with an existing
    database table or for other specific purposes.

    Attributes:
        Meta (class): Contains metadata for the model.
            - managed (bool): Indicates that Django should not manage the database table.
            - verbose_name (str): A human-readable name for the model in singular form.
            - verbose_name_plural (str): A human-readable name for the model in plural form.
    """
    class Meta:
        managed = False
        verbose_name = "Budget Dashboard"
        verbose_name_plural = "Budget Dashboard"





