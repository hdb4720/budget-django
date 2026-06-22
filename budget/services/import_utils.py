# budget/importers/import_utils.py

from typing import Optional

from budget.models import Account, Category


def get_or_create_account(name: str) -> Account:
    """
    Normalize and get/create an Account.

    - Strips whitespace
    - Rejects empty names
    - Sets short_name and type on first creation
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("Account name is required")

    account, _ = Account.objects.get_or_create(
        name=name,
        defaults={
            "short_name": name,
            "type": "Unknown",
        },
    )
    return account


def get_or_create_category_from_path(path: str) -> Category:
    """
    Create or fetch a hierarchical Category from a dotted path, e.g.:

        "Utilities.Electricity"
        "Housing.Rent"

    Ensures:
    - full_path is unique
    - parent/level are set correctly
    """
    parts = [p.strip() for p in (path or "").split(".") if p.strip()]
    if not parts:
        raise ValueError("Category path is required")

    parent: Optional[Category] = None
    full_path = ""

    for i, part in enumerate(parts):
        full_path = part if i == 0 else f"{full_path}.{part}"

        category, _ = Category.objects.get_or_create(
            full_path=full_path,
            defaults={
                "name": part,
                "parent": parent,
                "level": i,
            },
        )
        parent = category

    return parent
