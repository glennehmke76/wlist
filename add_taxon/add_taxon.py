#!/usr/bin/env python3
"""
add_taxon.py — Add one or more rows to wlist using the stored procedure wlist_add_row.

Features
- Uses existing psycopg2 connection from package_wlist.get_db_connection()
- All-or-nothing transaction (entire batch commits or rolls back)
- Dry-run mode to validate and capture server NOTICEs but roll back at the end
- Accepts CSV (friendly headers supported) or JSON input
- Performs pre-checks (required fields, is_ultrataxon in {0,1}, target exists, duplicate taxon_id)

Usage examples
- Dry run from CSV (no DB changes):
    python -m wlist.add_taxon --csv /path/to/new_rows.csv --dry-run
- Commit batch from JSON:
    python -m wlist.add_taxon --json /path/to/new_rows.json

CSV headers: you can use friendly headers (without p_ prefix) and they will be mapped.
Missing columns are sent as NULL.
"""
from __future__ import annotations

import argparse
import csv
import json
from typing import Iterable, Mapping

# Prefer package import when running as module, fall back to local import when run as script
try:  # pragma: no cover
    from wlist.package_wlist import get_db_connection  # type: ignore
except Exception:  # pragma: no cover
    from package_wlist import get_db_connection  # type: ignore

# Parameter order of the stored procedure wlist_add_row
PARAMS_ORDER = [
    "p_taxon_sort_target",
    "p_taxon_id",
    "p_is_ultrataxon",
    "p_taxon_level",
    "p_sp_id",
    "p_taxon_name",
    "p_taxon_scientific_name",
    "p_family_name",
    "p_family_scientific_name",
    "p_t_order",
    "p_population",
    "p_aust_rli_1990",
    "p_aust_rli_2000",
    "p_aust_rli_2010",
    "p_aust_rli",
    "p_bird_group",
    "p_supplementary",
    "p_avibase_id",
    "p_reference",
]

# Use named-argument notation with explicit casts so PostgreSQL can resolve types even when many NULLs are passed
CALL_SQL = (
    "CALL wlist_add_row("
    "p_taxon_sort_target := %s::integer, "
    "p_taxon_id := %s::varchar, "
    "p_is_ultrataxon := %s::smallint, "
    "p_taxon_level := %s::varchar, "
    "p_sp_id := %s::smallint, "
    "p_taxon_name := %s::varchar, "
    "p_taxon_scientific_name := %s::varchar, "
    "p_family_name := %s::varchar, "
    "p_family_scientific_name := %s::varchar, "
    "p_t_order := %s::varchar, "
    "p_population := %s::varchar, "
    "p_aust_rli_1990 := %s::smallint, "
    "p_aust_rli_2000 := %s::smallint, "
    "p_aust_rli_2010 := %s::smallint, "
    "p_aust_rli := %s::smallint, "
    "p_bird_group := %s::varchar, "
    "p_supplementary := %s::smallint, "
    "p_avibase_id := %s::varchar, "
    "p_reference := %s::text)"
)

REQUIRED = {"p_taxon_sort_target", "p_is_ultrataxon"}

# Friendly header mapping → procedure parameter names
HEADER_MAP = {
    # friendlier_name : procedure_param_name
    "taxon_sort_target": "p_taxon_sort_target",
    "taxon_id": "p_taxon_id",
    "is_ultrataxon": "p_is_ultrataxon",
    "taxon_level": "p_taxon_level",
    "sp_id": "p_sp_id",
    "taxon_name": "p_taxon_name",
    "taxon_scientific_name": "p_taxon_scientific_name",
    "family_name": "p_family_name",
    "family_scientific_name": "p_family_scientific_name",
    "order": "p_t_order",
    "t_order": "p_t_order",
    "population": "p_population",
    "aust_rli_1990": "p_aust_rli_1990",
    "aust_rli_2000": "p_aust_rli_2000",
    "aust_rli_2010": "p_aust_rli_2010",
    "aust_rli": "p_aust_rli",
    "bird_group": "p_bird_group",
    "bird_sub_group": "p_bird_group",  # backward compatibility with older header
    "supplementary": "p_supplementary",
    "avibase_id": "p_avibase_id",
    "reference": "p_reference",
}

INT_FIELDS = {
    "p_taxon_sort_target",
    "p_is_ultrataxon",
    "p_sp_id",
    "p_aust_rli_1990",
    "p_aust_rli_2000",
    "p_aust_rli_2010",
    "p_aust_rli",
    "p_supplementary",
}


def normalize_and_map_headers(row: Mapping[str, str | None]) -> dict:
    """Map friendly headers to proc params, trim strings, cast ints, blank→None."""
    out: dict = {}
    for key, val in row.items():
        if key is None:
            continue
        k = key.strip()
        if not k:
            continue
        pkey = HEADER_MAP.get(k, k)  # allow either friendly or p_* headers
        v = None if (val is None or str(val).strip() == "") else str(val).strip()
        out[pkey] = v
    # Cast integer-like fields
    for k in list(out.keys()):
        if out[k] is not None and k in INT_FIELDS:
            try:
                out[k] = int(out[k])
            except Exception as e:
                raise ValueError(f"Field {k} expects an integer, got {out[k]!r}") from e
    return out


def load_rows_from_csv(path: str) -> Iterable[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield normalize_and_map_headers(row)


# ------------------------- Pre-checks and validation ------------------------

def fetch_existing_taxon_sorts(conn) -> set[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT taxon_sort FROM wlist")
        return {r[0] for r in cur.fetchall()}


def fetch_existing_taxon_ids(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT taxon_id FROM wlist")
        return {r[0] for r in cur.fetchall() if r[0] is not None}


def validate_row_inputs(row: Mapping, existing_taxon_sorts: set[int], existing_taxon_ids: set[str]):
    # Required params present
    missing = [k for k in REQUIRED if row.get(k) is None]
    if missing:
        raise ValueError(f"Missing required parameter(s): {missing}")

    # is_ultrataxon must be 0 or 1
    try:
        is_u = int(row.get("p_is_ultrataxon"))
    except Exception as e:
        raise ValueError("p_is_ultrataxon must be integer 0 or 1") from e
    if is_u not in (0, 1):
        raise ValueError("p_is_ultrataxon must be 0 or 1")

    # If non-ultrataxon, a taxon_id must be provided (the proc enforces this too)
    if is_u != 1 and not row.get("p_taxon_id"):
        raise ValueError("For non-ultrataxon (p_is_ultrataxon != 1), p_taxon_id is required")

    # p_taxon_sort_target should exist (optional but recommended to protect ordering)
    tgt = row.get("p_taxon_sort_target")
    if tgt not in existing_taxon_sorts:
        raise ValueError(f"p_taxon_sort_target {tgt} does not exist in wlist")

    # Optional dup check: if caller provided taxon_id, avoid clashing with existing
    txid = row.get("p_taxon_id")
    if txid and txid in existing_taxon_ids:
        raise ValueError(f"p_taxon_id '{txid}' already exists in wlist")

    # sp_id sanity (if provided). The proc will auto-assign 5001–7999 if missing.
    sp_id = row.get("p_sp_id")
    if sp_id is not None:
        try:
            sp_int = int(sp_id)
        except Exception as e:
            raise ValueError("p_sp_id must be an integer if provided") from e
        if not (0 < sp_int < 10000):
            raise ValueError("p_sp_id looks invalid; expected a small positive integer")


def row_to_tuple(row: Mapping) -> tuple:
    return tuple(row.get(name) for name in PARAMS_ORDER)


# ---------------------------- Main batch function ---------------------------

def add_wlist_rows_psycopg2(
    rows: Iterable[Mapping],
    *,
    dry_run: bool = False,
    collect_notices: bool = True,
) -> dict:
    """
    All-or-nothing batch insert via CALL wlist_add_row(...).

    - dry_run=True: execute inside a transaction and roll back at the end.
    - collect_notices=True: return PostgreSQL NOTICEs emitted by the procedure.

    Returns a dict with keys: {"ok": bool, "row_results": list, "notices": list[str], "rolled_back"?: bool}.
    """
    results = []
    notices_all: list[str] = []

    with get_db_connection() as conn:
        conn.autocommit = False  # ensure we control the transaction

        # Pre-load state for validation (stable snapshot at txn start)
        existing_sorts = fetch_existing_taxon_sorts(conn)
        existing_ids = fetch_existing_taxon_ids(conn)

        try:
            with conn.cursor() as cur:
                for i, row in enumerate(rows, 1):
                    try:
                        validate_row_inputs(row, existing_sorts, existing_ids)
                        if collect_notices:
                            try:
                                conn.notices.clear()
                            except Exception:
                                pass
                        cur.execute(CALL_SQL, row_to_tuple(row))
                        # Update local caches for subsequent validations in this batch
                        tgt = int(row.get("p_taxon_sort_target"))
                        existing_sorts.add(tgt + 1)
                        txid = row.get("p_taxon_id")
                        if txid:
                            existing_ids.add(txid)
                        # Capture notices (may include auto sp_id/taxon_id)
                        row_notices = []
                        if collect_notices:
                            try:
                                if conn.notices:
                                    row_notices = conn.notices[:]
                                    notices_all.extend(row_notices)
                            except Exception:
                                pass
                        results.append({"row": i, "ok": True, "notices": row_notices})
                    except Exception as e:
                        # Any row error causes whole-batch failure (all-or-nothing)
                        results.append({"row": i, "ok": False, "error": str(e)})
                        raise
            if dry_run:
                conn.rollback()
                return {"ok": False, "row_results": results, "notices": notices_all, "rolled_back": True}
            else:
                conn.commit()
                return {"ok": all(r.get("ok") for r in results), "row_results": results, "notices": notices_all}
        except Exception:
            conn.rollback()
            return {"ok": False, "row_results": results, "notices": notices_all}


# --------------------------------- CLI -------------------------------------

def _load_rows_from_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON must be an object or an array of objects")
    # normalize headers if they are friendly
    return [normalize_and_map_headers(d) for d in data]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Add rows to wlist via stored procedure wlist_add_row")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", dest="csv_path", help="Path to CSV file with rows to insert")
    src.add_argument("--json", dest="json_path", help="Path to JSON file (list of objects)")
    ap.add_argument("--dry-run", action="store_true", help="Validate and show NOTICEs but roll back at the end")
    args = ap.parse_args(argv)

    if args.csv_path:
        rows = list(load_rows_from_csv(args.csv_path))
    else:
        rows = _load_rows_from_json(args.json_path)

    result = add_wlist_rows_psycopg2(rows, dry_run=args.dry_run, collect_notices=True)
    ok = result.get("ok", False) and not result.get("rolled_back", False)
    print(f"Batch OK: {ok}. Rows processed: {len(result['row_results'])}")
    if result.get("rolled_back"):
        print("NOTE: Dry-run performed; transaction was rolled back")
    # Per-row summary
    failed = [r for r in result["row_results"] if not r.get("ok")]
    if failed:
        print(f"Failures: {len(failed)}")
        for r in failed:
            print(f"  Row {r['row']}: {r.get('error')}")
    # Show server NOTICEs
    notices = result.get("notices", [])
    if notices:
        print("Server NOTICEs:")
        for n in notices:
            print(n.strip())

    return 0 if ok or args.dry_run else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
