from django.db import transaction
from django.db.models import F

from budget.models import Transaction
from budget.importer.persist.accounts import resolve_account
from budget.importer.persist.categories import resolve_category


# ---------------------------------------------------------
# Upsert a new transaction
# ---------------------------------------------------------
def upsert_transaction(tx: dict):
    """
    Insert or keep a transaction based on the UID:
        (account, category, trn_date, description, memo, amount, seq)

    Returns:
        (obj, created)
    """
    account = resolve_account(tx["account_name"])
    category = resolve_category(tx["category_path"])

    with transaction.atomic():
        obj, created = Transaction.objects.update_or_create(
            account=account,
            category=category,
            trn_date=tx["trn_date"],
            description=tx["description"],
            memo=tx["memo"],
            amount=tx["amount"],
            seq=tx["seq"],
            defaults={}
        )
        return obj, created


# ---------------------------------------------------------
# Delete a transaction by primary key
# ---------------------------------------------------------
def delete_transaction(row_id: int):
    Transaction.objects.filter(id=row_id).delete()
