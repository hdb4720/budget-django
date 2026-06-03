def build_current_import(rows):
    """
    Build UID+Seq for import rows.
    UID = (account, date, description, memo, category, amount, seq)
    """

    import_dict = {}
    uid_counts = {}

    for row in rows:
        base_uid = (
            row["account_name"],
            row["date"],
            row["description"],
            row.get("memo", ""),
            row["category_path"],
            row["amount"],
        )

        seq = uid_counts.get(base_uid, 0)
        uid_counts[base_uid] = seq + 1

        uid = base_uid + (seq,)

        # Store row with seq included
        row_with_seq = dict(row)
        row_with_seq["seq"] = seq

        import_dict[uid] = row_with_seq

    return import_dict


def build_db_uid_map(db_rows):
    """
    Build UID+Seq for DB rows using the seq stored in the DB.
    """

    uid_map = {}

    for row in db_rows:
        uid = (
            row["account_name"],
            row["date"],
            row["description"],
            row["memo"] or "",
            row["category_path"],
            row["amount"],
            row["seq"],  # <-- use DB seq directly
        )

        uid_map[uid] = row

    return uid_map
