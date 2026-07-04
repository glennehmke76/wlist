#%%
"""
Ingest the edited wlist Excel into the database as a new table with the same schema as dcoredb.public.wlist.

Default source Excel: /Users/glennehmke/Downloads/wlist.xlsx
Default target table: public.wlist_edited

Usage examples:
  python -m wlist.ingest_edited_wlist \
      --xlsx "/Users/glennehmke/Downloads/wlist.xlsx" \
      --table "wlist_edited"

Environment variables for DB connection (same as other wlist tools):
  DCORE_HOST, DCORE_DB, DCORE_USER, DCORE_PASSWORD, DCORE_PORT
"""
#%%
import argparse
import os
import sys
from typing import List, Sequence
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras as pgx

# Import get_db_connection whether run as module or script
try:  # when run as package module
    from .package_wlist import get_db_connection
except Exception:  # when run directly
    from package_wlist import get_db_connection  # type: ignore

DEFAULT_XLSX = "/Users/glennehmke/Downloads/wlist.xlsx"
DEFAULT_TABLE = "wlist_edited"
SOURCE_TABLE = "wlist"  # reference schema/table to clone
DEFAULT_SCHEMA = "public"


def _fqtn(schema: str, table: str) -> str:
    return f'"{schema}"."{table}"'


def get_source_columns(conn, schema: str, table: str) -> List[str]:
    sql = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (schema, table))
        rows = cur.fetchall()
    return [r[0] for r in rows]


def schema_exists(conn, schema: str) -> bool:
    sql = "SELECT 1 FROM pg_namespace WHERE nspname = %s LIMIT 1;"
    with conn.cursor() as cur:
        cur.execute(sql, (schema,))
        return cur.fetchone() is not None


def table_exists(conn, schema: str, table: str) -> bool:
    sql = (
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = %s LIMIT 1;"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (schema, table))
        return cur.fetchone() is not None


def get_row_count(conn, schema: str, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {_fqtn(schema, table)};")
        (n,) = cur.fetchone()
    return int(n)


def validate_wlist_update(conn, public_schema: str, table: str, edited_table: str) -> tuple[bool, list[str]]:
    messages: list[str] = []
    ok = True

    if not table_exists(conn, public_schema, table):
        messages.append(f"Missing source table: {public_schema}.{table}")
        return False, messages

    if not table_exists(conn, public_schema, edited_table):
        messages.append(f"Missing edited table: {public_schema}.{edited_table}")
        ok = False
    else:
        src_cols = get_source_columns(conn, public_schema, table)
        edt_cols = get_source_columns(conn, public_schema, edited_table)
        if src_cols != edt_cols:
            messages.append(
                "Column mismatch between source and edited tables (order or names differ). "
                f"source={src_cols} edited={edt_cols}"
            )
            ok = False
        else:
            messages.append("Column check: OK")
        try:
            n_src = get_row_count(conn, public_schema, table)
            n_edt = get_row_count(conn, public_schema, edited_table)
            messages.append(f"Row counts — source: {n_src}, edited: {n_edt}")
        except Exception as e:
            messages.append(f"Row count check failed: {e}")
            ok = False

    return ok, messages


def ensure_target_table(conn, schema: str, source_table: str, target_table: str, drop_if_exists: bool = True) -> None:
    fq_target = _fqtn(schema, target_table)
    fq_source = _fqtn(schema, source_table)
    with conn.cursor() as cur:
        if drop_if_exists:
            cur.execute(f"DROP TABLE IF EXISTS {fq_target};")
        # Clone structure including defaults, constraints, etc.
        cur.execute(f"CREATE TABLE {fq_target} (LIKE {fq_source} INCLUDING ALL);")
    conn.commit()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Lower-case, strip, and replace spaces with underscores to better align with SQL identifiers
    mapping = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
    return df.rename(columns=mapping)


def align_dataframe_to_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    df_cols = list(df.columns)
    # Keep only known columns, add any missing as NA, order to match `columns`
    present = [c for c in columns if c in df_cols]
    missing = [c for c in columns if c not in df_cols]
    extra = [c for c in df_cols if c not in columns]
    if extra:
        print(f"Warning: dropping {len(extra)} extra columns not in source schema: {extra}", file=sys.stderr)
    out = df[present].copy()
    for c in missing:
        out[c] = pd.NA
    # reorder
    out = out[list(columns)]
    return out


def bulk_insert(conn, schema: str, table: str, df: pd.DataFrame, page_size: int = 1000) -> int:
    if df.empty:
        return 0
    cols = list(df.columns)
    records = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]
    tmpl = "(" + ", ".join(["%s"] * len(cols)) + ")"
    sql = f"INSERT INTO {_fqtn(schema, table)} (" + ", ".join([f'\"{c}\"' for c in cols]) + ") VALUES %s"
    with conn.cursor() as cur:
        pgx.execute_values(cur, sql, records, template=tmpl, page_size=page_size)
    conn.commit()
    return len(records)


def archive_and_update(
    conn,
    public_schema: str = "public",
    table: str = "wlist",
    edited_table: str = "wlist_edited",
    backup_schema: str = "backup",
    date_suffix: str | None = None,
) -> None:
    """
    Replace archive_and_update with a single SQL DO block transaction that:
      - Creates a dated backup table in the backup schema from public.wlist
      - Truncates public.wlist
      - Temporarily disables triggers, inserts from public.wlist_edited, re-enables triggers
      - Drops public.wlist_edited
    This follows the provided SQL exactly, using CURRENT_DATE for the backup suffix.
    Note: function parameters are retained for CLI compatibility but are not used by the SQL block.
    """
    sql = r'''
DO $$
DECLARE
    v_backup_table_name TEXT;
BEGIN
    -- Generate dynamic backup table name with current date
    v_backup_table_name := 'wlist_' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD');

    -- Create backup table in backup schema
    EXECUTE FORMAT('CREATE TABLE backup.%I AS SELECT * FROM public.wlist', v_backup_table_name);
    RAISE NOTICE 'Backup created: backup.%', v_backup_table_name;

    -- 1. Truncate wlist
    TRUNCATE TABLE public.wlist;

    -- 2. Disable trigger on wlist temporarily
    ALTER TABLE public.wlist DISABLE TRIGGER ALL;

    -- 3. Insert wlist_edited to wlist
    INSERT INTO public.wlist
    SELECT * FROM public.wlist_edited;

    -- 4. Re-enable trigger
    ALTER TABLE public.wlist ENABLE TRIGGER ALL;

    -- 5. Drop wlist_edited
    DROP TABLE public.wlist_edited;

    RAISE NOTICE 'wlist update completed successfully.';

EXCEPTION
    WHEN OTHERS THEN
        -- Re-enable triggers in case of error
        ALTER TABLE public.wlist ENABLE TRIGGER ALL;
        RAISE EXCEPTION 'Error updating wlist: %', SQLERRM;
END;
$$;
'''
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest edited wlist Excel as wlist_edited (schema cloned from wlist)")
    p.add_argument("--xlsx", default=DEFAULT_XLSX, help="Path to edited Excel file (default: %(default)s)")
    p.add_argument("--table", default=DEFAULT_TABLE, help="Target table name (default: %(default)s)")
    p.add_argument("--schema", default=DEFAULT_SCHEMA, help="Target schema (default: %(default)s)")
    p.add_argument("--source-table", default=SOURCE_TABLE, help="Source table to clone (default: %(default)s)")
    p.add_argument("--sheet", default=0, help="Excel sheet index/name (default: first sheet)")
    p.add_argument("--archive-and-update", action="store_true", help="After ingesting into wlist_edited, archive public.wlist to backup schema and replace public.wlist with edited data")
    p.add_argument("--backup-schema", default="backup", help="Schema for backups (default: %(default)s)")
    p.add_argument("--date-suffix", default=None, help="Date suffix for backup table name (default: YYYYMMDD today)")
    p.add_argument("--validate-only", action="store_true", help="Only run validation checks and exit (non-zero on failure)")
    args = p.parse_args(argv)

    # If only validating, skip reading Excel
    if args.validate_only:
        with get_db_connection() as conn:
            ok, msgs = validate_wlist_update(conn, args.schema, args.source_table, args.table)
            for m in msgs:
                print(m)
            return 0 if ok else 4

    xlsx_path = os.path.expanduser(str(args.xlsx))
    if not os.path.isfile(xlsx_path):
        print(f"Error: Excel file not found: {xlsx_path}", file=sys.stderr)
        return 2

    print(f"Reading Excel: {xlsx_path}", file=sys.stderr)
    df = pd.read_excel(xlsx_path, sheet_name=args.sheet, dtype=str)  # read as strings to avoid unintended casts
    df = normalize_columns(df)

    with get_db_connection() as conn:
        # Discover source (wlist) column order
        src_cols = get_source_columns(conn, args.schema, args.source_table)
        if not src_cols:
            print(f"Error: could not find source table {args.schema}.{args.source_table}", file=sys.stderr)
            return 3
        # Create target table
        ensure_target_table(conn, args.schema, args.source_table, args.table)
        # Align dataframe
        df_aligned = align_dataframe_to_columns(df, src_cols)
        # Insert
        print(f"Inserting {len(df_aligned)} rows into {args.schema}.{args.table}...", file=sys.stderr)
        n = bulk_insert(conn, args.schema, args.table, df_aligned)
        print(f"Done. Inserted {n} rows into {args.schema}.{args.table}.")

        if args.archive_and_update:
            print(
                f"Archiving {args.schema}.{args.source_table} to {args.backup_schema}.{args.source_table}_<date> and replacing live table...",
                file=sys.stderr,
            )
            archive_and_update(
                conn,
                public_schema=args.schema,
                table=args.source_table,
                edited_table=args.table,
                backup_schema=args.backup_schema,
                date_suffix=args.date_suffix,
            )
            print("Archive and update complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
