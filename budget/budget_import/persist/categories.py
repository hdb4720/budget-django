from django.db import transaction
from django.core.exceptions import ValidationError
from budget.models import Category

PATH_SEP = ":"


from django.db import transaction
from budget.models import Category


def resolve_category(path: str) -> Category:
    """
    Given a category path like 'Living:Groceries' or 'House:Maintenance:Roof',
    return the deepest Category object.
    Create intermediate parent categories if they do not exist.
    """
    if not path or not path.strip():
        path = "Uncategorized"

    path = path.strip()
    parts = [p.strip() for p in path.split(":") if p.strip()]

    parent = None
    full_path = ""

    with transaction.atomic():
        for level, part in enumerate(parts):
            full_path = part if level == 0 else f"{full_path}:{part}"

            category, created = Category.objects.get_or_create(
                full_path=full_path,
                defaults={
                    "name": part,
                    "parent": parent,
                    "level": level,
                }
            )

            parent = category

    return category
