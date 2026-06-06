import polars as pl

from datetime import datetime
from decimal import Decimal


def parse_excel(file, layout):
    """
    Generic layout-driven Excel parser.
    Returns:
        df_rows: list of normalized transaction dicts
        df_start: report start date (from metadata row)
        df_end: report end date (from metadata row)
    """
    # -----------------------------------------------------
    # Load raw sheet and build report sections
    # -----------------------------------------------------
    data = file.read()
    df_raw = pl.read_excel(data, sheet_name="Report", has_header=False)
    
    df_title_row = layout.get("title_row") - 1
    df_date_row = layout.get("date_range_row") - 1
    df_header_row = layout.get("header_row") - 1
    df_detail_row = layout.get("detail_row") - 1
    df_total_lines = layout.get("total_lines")
    
    df_title = df_raw[df_title_row, 0] if df_title_row is not None else None
    
    df_date = df_raw[df_date_row, 0] if df_date_row is not None else None
    
    # -----------------------------------------------------
    # Extract date range from metadata row
    # -----------------------------------------------------
    if df_date is not None:
        df_start, df_end = parse_date_range(df_date, layout)
    else:
        df_start = None
        df_end = None
    
    # -----------------------------------------------------
    # Extract data header from metadata row
    # -----------------------------------------------------
    raw_header = df_raw.row(df_header_row)

    header_list = []
    for i, h in enumerate(raw_header):
        if h is None:
            header_list.append(f"unnamed_{i}")
        else:
            cleaned = (
                str(h)
                .strip()
                .lower()
                .replace(" ", "_")
            )
            header_list.append(cleaned)

    # -----------------------------------------------------
    # Extract data detail from metadata rows
    # -----------------------------------------------------
    df_detail = df_raw[df_detail_row : -df_total_lines]
    
    # -----------------------------------------------------
    # Assign header row as column names
    # -----------------------------------------------------
    df_detail = df_detail.rename(
        dict(zip(df_detail.columns, header_list))
    )
    # -----------------------------------------------------
    # Extract beginning and ending balances
    # -----------------------------------------------------
    df_beginning_balance = df_raw[df_detail_row-1, 1]
    
    df_ending_balance = (
        df_raw
        .select(pl.col(df_raw.columns[1]).drop_nulls().last())
        .item()
    )
    
    # -----------------------------------------------------
    # Normalize column names
    # -----------------------------------------------------
    df_detail.columns = normalize_columns(df_detail.columns, layout)

    # -----------------------------------------------------
    # Validate required columns
    # -----------------------------------------------------
    validate_columns(df_detail, layout)

    # -----------------------------------------------------
    # Apply splits, defaults and data validation
    # -----------------------------------------------------
    df_detail = handle_splits(df_detail)
    df_detail = apply_defaults(df_detail)
    validate_rows(df_detail, layout)

    # -----------------------------------------------------
    # Build internal transaction rows
    # -----------------------------------------------------
    df_rows = build_transactions(df_detail, layout)

    return df_rows, df_start, df_end


def parse_date_range(date_text, layout):
    """
    Extract start and end dates from a string like:
    '01/01/2026 through 03/31/2026'
    """
    if not isinstance(date_text, str):
        raise ValueError("Date range row does not contain text")

    keyword = layout["date_range_pattern"]  # 'through'
    if keyword not in date_text.lower():
        raise ValueError("Could not find date range keyword in report")

    left, right = date_text.lower().split(keyword)
    start = left.strip()
    end = right.strip()

    # Let Python infer the date format
    df_start = datetime.strptime(start, "%m/%d/%Y").date()
    df_end = datetime.strptime(end, "%m/%d/%Y").date()

    return df_start, df_end


def normalize_columns(columns, layout):
    rules = layout["column_normalization"]
    normalized = []

    for col in columns:
        c = str(col)

        if rules.get("strip"):
            c = c.strip()
        if rules.get("lower"):
            c = c.lower()
        if rules.get("spaces_to_underscores"):
            c = c.replace(" ", "_")

        normalized.append(c)

    return normalized


def validate_columns(df, layout):
    required = layout["required_columns"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")


def handle_splits(df):
    last_account = None
    last_date = None
    last_desc = None

    out = []
    for row in df.to_dicts():
        raw_account = row["account"]
        raw_date = row["date"]
        raw_desc = row["description"]

        is_split = (
            raw_account is None and
            raw_date is None and
            raw_desc is None
        )

        if is_split:
            account = last_account
            date_val = last_date
            desc = last_desc
        else:
            account = raw_account
            date_val = raw_date
            desc = raw_desc

            last_account = account
            last_date = date_val
            last_desc = desc

        row = row.copy()
        row["account"] = account
        row["date"] = date_val
        row["description"] = desc
        out.append(row)

    return pl.DataFrame(out)


# import polars as pl

def apply_defaults(df):
    return df.with_columns(
        pl.col("category")
            .fill_null("Uncategorized")
            .replace("", "Uncategorized"),

        pl.col("description")
            .fill_null("")
            .replace("", ""),

        pl.col("memo")
            .fill_null("")
            .replace("", ""),
    )


def validate_rows(df, layout):
    required = layout["required_columns"]

    bad = df.filter(
        pl.any_horizontal([pl.col(c).is_null() for c in required])
    )
    if not bad.is_empty:
        raise ValueError(
            "Rows missing required values after split handling and defaults:\n"
            f"{bad}"
        )


def build_transactions(df, layout):
    """
    Convert the cleaned DataFrame into a list of internal transaction dicts,
    using the layout's column_map to translate report columns → internal fields.
    """
    df_rows = []
    seq_map = {}

    colmap = layout["column_map"]
    defaults = layout.get("column_defaults", {})

    for row in df.to_dicts():
        tx = {}

        # -----------------------------
        # 1. Map report columns → internal fields
        # -----------------------------
        for source_col, target_field in colmap.items():
            if source_col in row and row[source_col] is not None:
                tx[target_field] = row[source_col]
            else:
                tx[target_field] = defaults.get(source_col, "")

        # -----------------------------
        # 2. Normalize category
        # -----------------------------
        if "category_path" in tx:
            cat = str(tx["category_path"]).strip()
            tx["category_path"] = cat if cat else defaults.get("category", "Uncategorized")

        # -----------------------------
        # 3. Normalize date
        # -----------------------------
        if "date" in tx:
            tx["date"] = datetime.strptime(tx["date"], "%Y-%m-%d %H:%M:%S").date()

        # -----------------------------
        # 4. Normalize amount → Decimal
        # -----------------------------
        if "amount" in tx:
            tx["amount"] = Decimal(str(tx["amount"]))

        # -----------------------------
        # 5. Normalize description/memo
        # -----------------------------
        for field in ("description", "memo"):
            if field in tx:
                tx[field] = str(tx[field]).strip()

        # -----------------------------
        # 6. Apply seq logic
        # -----------------------------
        key = (
            tx.get("account_name", ""),
            tx.get("category_path", ""),
            tx.get("date", ""),
            tx.get("description", ""),
            tx.get("memo", ""),
            tx.get("amount", ""),
        )

        seq = seq_map.get(key, 0)
        seq_map[key] = seq + 1
        tx["seq"] = seq

        # -----------------------------
        # 7. Append to results
        # -----------------------------
        df_rows.append(tx)

    return df_rows

