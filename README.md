Wlist tools: ingest, validate, archive and update

These utilities help you ingest an edited wlist Excel, validate it against the live table, and safely replace the live table with full backup and fallback.

Database and schemas
- Database: dcoredb
- Live schema/table: public.wlist
- Edited staging table (created by ingest): public.wlist_edited (configurable)
- Preferred backup schema: backup (falls back to public if backup is unavailable)

DB connection
Set environment variables (defaults in parentheses):
- DCORE_HOST (localhost)
- DCORE_DB (dcoredb)
- DCORE_USER (glennehmke)
- DCORE_PASSWORD (no default — set via env var or `~/.pgpass`)
- DCORE_PORT (5432)

Commands (CLI)
- Validate only (no changes). Exits 0 if OK, 4 if validation fails.

```bash
python -m wlist.ingest.validate_wlist_update --schema public --table wlist --edited-table wlist_edited
```

- Or via the ingest module:

```bash
python -m wlist.ingest.ingest_edited_wlist --schema public --source-table wlist --table wlist_edited --validate-only
```

- Ingest edited Excel to a staging table matching the live schema:

```bash
python -m wlist.ingest.ingest_edited_wlist \
    --xlsx "/Users/glennehmke/Downloads/wlist.xlsx" \
    --schema public \
    --source-table wlist \
    --table wlist_edited
```

- Ingest and then archive+replace the live table in one go:

```bash
python -m wlist.ingest.ingest_edited_wlist \
    --xlsx /path/to/wlist.xlsx \
    --schema public --source-table wlist --table wlist_edited \
    --archive-and-update --backup-schema backup --date-suffix 20260317
```

What archive_and_update does
1) Validates the edited table has the same columns (same order/names) as the live table and reports row counts.
2) Attempts to create a full-data backup copy of public.wlist to backup.wlist_YYYYMMDD.
   - If the backup schema cannot be used (e.g., permissions), it falls back to creating public.wlist_YYYYMMDD.
3) Truncates public.wlist (preserving its keys, indexes, and triggers) and inserts rows from public.wlist_edited in explicit column order.
4) Verifies row count after insert (>0), otherwise restores public.wlist from the backup and aborts.
5) Drops public.wlist_edited on success.

Notes and tips
- Column alignment: The ingest step normalizes Excel column headers (lowercase, spaces to underscores) and aligns to the live schema columns, dropping extras and adding missing as NULLs.
- Excel reading: By default reads sheet index 0 and coerces all values to strings to avoid unintended type conversions. Override with --sheet if needed.
- Fallback backup location: You can safely pass --backup-schema backup; if creation of backup.wlist_YYYYMMDD fails, the tool will automatically create public.wlist_YYYYMMDD instead and continue.
- Date suffix: Omit --date-suffix to use today’s date (YYYYMMDD). Provide a custom suffix to align with a deployment window.
- Exit codes: validate-only returns 0 (OK) or 4 (failed). The ingest script returns non-zero on error conditions.

Examples (CLI)
- Quick safety check before any changes:

```bash
python -m wlist.ingest.validate_wlist_update --schema public --table wlist --edited-table wlist_edited
```

- One-shot ingest + archive + replace using today’s date:

```bash
python -m wlist.ingest.ingest_edited_wlist --xlsx /Users/glennehmke/Downloads/wlist.xlsx \
    --schema public --source-table wlist --table wlist_edited \
    --archive-and-update --backup-schema backup
```

- Use a custom date suffix (e.g., for 2026-03-17):

```bash
python -m wlist.ingest.ingest_edited_wlist --xlsx /path/to/wlist.xlsx \
    --schema public --source-table wlist --table wlist_edited \
    --archive-and-update --backup-schema backup --date-suffix 20260317
```

Python usage (API)
- Run a quick check via the Python API (uses package_wlist.get_db_connection):

```python
from wlist.package_wlist import get_db_connection, fetch_dataframe

# Optional: ensure env vars DCORE_HOST/DB/USER/PASSWORD/PORT are set
# import os; os.environ["DCORE_DB"] = "dcoredb"

# 1) Connect and count rows in the live table
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.wlist;")
        (n_rows,) = cur.fetchone()
        print(f"public.wlist rows: {n_rows}")

# 2) Or fetch into a DataFrame directly
import pandas as pd

df = fetch_dataframe("SELECT taxon_id, taxon_name FROM public.wlist LIMIT 5;")
print(df)
```

Modules overview
- wlist/ingest_edited_wlist.py
  - CLI to read Excel, create a staging table cloned from public.wlist, bulk-insert rows, optionally archive_and_update the live table.
  - Flags: --xlsx, --table, --schema, --source-table, --sheet, --archive-and-update, --backup-schema, --date-suffix, --validate-only
- wlist/validate_wlist_update.py
  - Standalone validator that compares schema and reports row counts before replacing the live table.
- wlist/package_wlist.py
  - Utilities to export wlist data to CSV/SQL and to obtain a DB connection (get_db_connection).
