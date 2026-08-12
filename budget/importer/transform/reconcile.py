from typing import Dict, Tuple, Any, List


# ---------------------------------------------------------
# Reconcile import vs database
# ---------------------------------------------------------
def reconcile(
    current_import: Dict[Tuple, Dict[str, Any]],
    current_db: Dict[Tuple, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Tuple]]:
    """
    Compare the UID-keyed dicts:
        current_import : { UID : row }
        current_db     : { UID : row }

    Returns:
        inserts : list of row dicts to insert
        deletes : list of UID tuples to delete
    """

    import_uids = set(current_import.keys())
    db_uids = set(current_db.keys())

    # Rows in import but not in DB → INSERT
    inserts = [current_import[uid] for uid in (import_uids - db_uids)]

    # Rows in DB but not in import → DELETE
    deletes = list(db_uids - import_uids)

    return inserts, deletes

def build_uid_db(row):
    return (
        row.account.name,
        row.category.full_path,
        row.trn_date,
        row.description,
        row.memo or "",
        row.amount,
        row.seq,
    )

def build_uid_df(row):
    return (
        row["account_name"],
        row["category_path"],
        row["trn_date"],
        row["description"],
        row.get("memo", "") or "",
        row["amount"],
        row["seq"],
    )

def natural_key(row):
    return (
        row["account_name"],
        row["category_path"],
        row["trn_date"],
        row["amount"],
        row["description"],
        row["memo"],
        row["seq"],
    )


def diff_rows(old_row, new_row):
    diffs = {}
    for field in ["account_name", "category_path", "trn_date", "description", "memo", "amount", "seq"]:
        old_val = getattr(old_row, field, None)
        new_val = new_row.get(field)
        if old_val != new_val:
            diffs[field] = {"old": old_val, "new": new_val}
    return diffs


