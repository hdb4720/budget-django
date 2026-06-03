from budget.models import Transaction
from budget.budget_import.persist.posting import post_transactions
from .reconcile import (
    build_uid_db, 
    build_uid_df, 
    natural_key, 
    diff_rows
)


def run_import(df_rows, df_start, df_end, dry_run=False, display_results=False):

    # ---------------------------------------------------------
    # 1. Fetch DB rows in the declared date range
    # ---------------------------------------------------------
    db_rows = Transaction.objects.filter(
        date__gte=df_start,
        date__lte=df_end
    )

    # ---------------------------------------------------------
    # 2. Build UID maps
    # ---------------------------------------------------------
    db_map = {build_uid_db(row): row for row in db_rows}
    df_map = {build_uid_df(row): row for row in df_rows}

    db_uids = set(db_map.keys())
    df_uids = set(df_map.keys())

    uids_to_insert = df_uids - db_uids
    uids_to_delete = db_uids - df_uids

    rows_to_insert = [
        {
            "account_name": row["account_name"],
            "category_path": row["category_path"],
            "date": row["date"],
            "description": row["description"],
            "memo": row["memo"],
            "amount": row["amount"],
            "seq": row["seq"],
        }
        for row in (df_map[uid] for uid in uids_to_insert)
    ]

    rows_to_delete = [
        {
            "id": row.id,
            "account_name": row.account.name,
            "category_path": row.category.full_path if row.category else None,
            "date": row.date,
            "description": row.description,
            "memo": row.memo,
            "amount": row.amount,
            "seq": row.seq,
        }
        for row in (db_map[uid] for uid in uids_to_delete)
    ]

    # ---------------------------------------------------------
    # 3. Apply DB changes (unless dry run)
    # ---------------------------------------------------------
    if not dry_run:
        summary = post_transactions(rows_to_insert, rows_to_delete)
    else:
        summary = {
            "inserted": len(rows_to_insert),
            "deleted": len(rows_to_delete),
            "kept": 0,
            "total_imported": len(rows_to_insert),
        }

    # ---------------------------------------------------------
    # 4. Return results
    # ---------------------------------------------------------
    return {
        "dry_run": dry_run,
        "display_results": display_results,
        "df_start": df_start,
        "df_end": df_end,
        "rows_to_insert": rows_to_insert if display_results else None,
        "rows_to_delete": rows_to_delete if display_results else None,
        "summary": summary,
    }
