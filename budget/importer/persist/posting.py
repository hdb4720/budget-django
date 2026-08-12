from django.db import transaction
from budget.importer.persist.accounts import resolve_account
from budget.importer.persist.categories import resolve_category
from budget.importer.persist.transactions import upsert_transaction, delete_transaction


def post_transactions(rows_to_insert, rows_to_delete):
    """
    Apply the importer diff to the database.

    rows_to_insert: list of tx dicts from the parser
    rows_to_delete: list of dicts containing {"id": <pk>} for deletion

    Returns:
        {
            "inserted": int,
            "kept": int,
            "deleted": int,
            "total_imported": int,
        }
    """

    inserted = 0
    kept = 0
    deleted = 0

    # ---------------------------------------------------------
    # 1. Insert or keep transactions
    # ---------------------------------------------------------
    for tx in rows_to_insert:
        obj, created = upsert_transaction(tx)

        if created:
            inserted += 1
        else:
            kept += 1

    # ---------------------------------------------------------
    # 2. Delete transactions that disappeared from the import
    # ---------------------------------------------------------
    for row in rows_to_delete:
        delete_transaction(row["id"])
        deleted += 1

    # ---------------------------------------------------------
    # 3. Return summary
    # ---------------------------------------------------------
    return {
        "inserted": inserted,
        "kept": kept,
        "deleted": deleted,
        "total_imported": inserted + kept,
    }
