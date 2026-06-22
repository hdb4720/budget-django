from datetime import date
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
        return self.filter(date__gte=period.start, date__lte=period.end)

class BudgetQuerySet(models.QuerySet):
    def for_period(self, period):
        return self.filter(date__gte=period.start, date__lte=period.end)

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
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    date = models.DateField()
    description = models.CharField(max_length=200)
    memo = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    seq = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionQuerySet.as_manager()    
    
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.description} - {self.category} - {self.amount}"

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
        related_name="budgets",
    )

    # For PLANNED: the due date of the obligation
    # For TRANSIENT: the anchor date used to assign this budget to a period
    date = models.DateField()

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    type = models.CharField(
        max_length=20,
        choices=BudgetType.choices,
    )

    # Optional: which account is expected to satisfy this budget
    account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BudgetQuerySet.as_manager()

    class Meta:
        ordering = ["date", "category__full_path"]

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



