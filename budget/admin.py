from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html


from .models import (
    Account,
    Category,
    Transaction,
    Budget,
    PeriodScheme,
    Period,
    ImporterEntry,
    BudgetDashboardEntry,
)

# -----------------------------
# Account Admin
# -----------------------------
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "type", "institution")
    search_fields = ("name", "short_name", "institution")


# -----------------------------
# Category Admin
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("full_path", "name", "parent", "level")
    search_fields = ("full_path", "name")
    list_filter = ("level",)


# -----------------------------
# Transaction Admin
# -----------------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "trn_date",
        "description",
        "category",
        "memo",
        "amount",
    )
    list_filter = ("account", "category", "trn_date")
    search_fields = ("description", "memo", "category__name")
    change_list_template = "admin/budget/transaction_changelist.html"

# -----------------------------
# Budget Admin
# -----------------------------
@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("due_date", "category", "amount", "account", "type")
    list_filter = ("due_date", "category", "account", "type")
    search_fields = ("category__name", "notes", "type")


# -----------------------------
# Period + PeriodScheme Admin
# -----------------------------
class PeriodInline(admin.TabularInline):
    model = Period
    extra = 0
    ordering = ("sequence",)
    readonly_fields = ("sequence", "start", "end", "label")
    can_delete = False


@admin.register(PeriodScheme)
class PeriodSchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "scheme_type", "start_date", "end_date")
    list_filter = ("scheme_type",)
    search_fields = ("name",)
    inlines = [PeriodInline]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "scheme_type", "notes")}),
        ("Date Range", {"fields": ("start_date", "end_date")}),
        (
            "Rules",
            {
                "fields": (
                    "monthly_interval",
                    "weekly_interval",
                    "nth_weekday",
                    "nth_ordinal",
                    "cut_day",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        from budget.services.period_persistence import create_periods_for_scheme

        super().save_model(request, obj, form, change)
        if not change:
            create_periods_for_scheme(obj)


@admin.register(ImporterEntry)
class ImporterAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse("transaction_import"))


@admin.register(BudgetDashboardEntry)
class BudgetDashboardAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse("budget_dashboard"))




