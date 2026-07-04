"""
Validate that an edited wlist table can safely replace the live table.

Usage examples:
  python -m wlist.validate_wlist_update --schema public --table wlist --edited-table wlist_edited

Exit codes:
  0 = validation OK
  4 = validation failed
"""
from __future__ import annotations

import argparse
from typing import Sequence

try:
    from .package_wlist import get_db_connection
    from .ingest_edited_wlist import validate_wlist_update
except Exception:
    # When run directly
    from package_wlist import get_db_connection  # type: ignore
    from ingest_edited_wlist import validate_wlist_update  # type: ignore


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate wlist edited table against source table")
    p.add_argument("--schema", default="public", help="Schema containing tables (default: %(default)s)")
    p.add_argument("--table", default="wlist", help="Source table to compare (default: %(default)s)")
    p.add_argument("--edited-table", default="wlist_edited", help="Edited table to validate (default: %(default)s)")
    args = p.parse_args(argv)

    with get_db_connection() as conn:
        ok, msgs = validate_wlist_update(conn, args.schema, args.table, args.edited_table)
        for m in msgs:
            print(m)
        return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
