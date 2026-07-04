#!/usr/bin/env python3
"""
Find unmatched entries between two CSV files by a key column (default: taxon_id).

Defaults are set to the user's wlist export locations so this can be run directly:

    python scripts/find_unmatched_taxon_ids.py \
        --alivlist "/Users/glennehmke/MEGA/Taxonomy/wlist/wlist_alivlist_master.csv" \
        --core "/Users/glennehmke/MEGA/Taxonomy/wlist/wlist_core.csv"

It will print a summary to stdout and write two CSVs with the full rows for unmatched entries:
- unmatched_in_core_not_in_alivlist.csv
- unmatched_in_alivlist_not_in_core.csv

Use --output-dir to choose where to save the unmatched CSVs (defaults to the directory
of the first provided file that exists, falling back to the current working directory).

Notes
- taxon_id values are normalized as strings, stripped of whitespace; empty values are ignored.
- The writer preserves the column order of each source file independently.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List, Tuple, Set

import pandas as pd

# Import package_wlist for DB connection and query, whether run as module or script
try:  # when run as part of package
    from . import package_wlist as _pw
except Exception:  # when run as a standalone script
    import package_wlist as _pw  # type: ignore

DEFAULT_ALIVLIST = "/Users/glennehmke/MEGA/Taxonomy/wlist/wlist_alivlist_master.csv"
DEFAULT_CORE = "wlist"


def _normalize_id(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    return s


def read_csv_indexed(path: str, id_column: str) -> Tuple[Dict[str, dict], List[str]]:
    """Read CSV and return a mapping id->row and the fieldnames.

    Skips rows missing the id_column or with empty/invalid IDs.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"CSV not found: {path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"No header found in CSV: {path}")
        if id_column not in reader.fieldnames:
            raise KeyError(
                f"Column '{id_column}' not found in {path}. Columns: {', '.join(reader.fieldnames)}"
            )
        index: Dict[str, dict] = {}
        for row in reader:
            key = _normalize_id(row.get(id_column))
            if key is None:
                continue
            # Keep the first occurrence; warn if duplicates across different rows
            if key in index:
                # Only warn if the row differs materially
                if row != index[key]:
                    print(
                        f"Warning: duplicate {id_column}='{key}' in {os.path.basename(path)} with differing rows; keeping first.",
                        file=sys.stderr,
                    )
                continue
            index[key] = row
    return index, reader.fieldnames  # type: ignore[arg-type]


def df_indexed(df: pd.DataFrame, id_column: str) -> Tuple[Dict[str, dict], List[str]]:
    """Index a DataFrame by the given id_column, returning mapping and ordered columns.

    Behaves like read_csv_indexed: skips missing/empty IDs and keeps first occurrence.
    """
    if id_column not in df.columns:
        raise KeyError(
            f"Column '{id_column}' not found in DataFrame. Columns: {', '.join(map(str, df.columns))}"
        )
    fields: List[str] = list(map(str, df.columns))
    index: Dict[str, dict] = {}
    for _, row in df.iterrows():
        val = row[id_column]
        key = _normalize_id(val)
        if key is None:
            continue
        if key in index:
            # Only warn if rows materially differ
            row_dict = {c: row[c] for c in df.columns}
            if row_dict != index[key]:
                print(
                    f"Warning: duplicate {id_column}='{key}' in DataFrame with differing rows; keeping first.",
                    file=sys.stderr,
                )
            continue
        # Convert pandas types to native Python where reasonable
        row_dict = {c: (None if pd.isna(row[c]) else row[c]) for c in df.columns}
        index[key] = row_dict
    return index, fields


def ensure_output_dir(provided: str | None, *input_paths: str) -> str:
    if provided:
        os.makedirs(provided, exist_ok=True)
        return provided
    for p in input_paths:
        if p and os.path.isfile(p):
            d = os.path.dirname(os.path.abspath(p))
            if d:
                return d
    return os.getcwd()


def write_rows(path: str, rows: List[dict], fieldnames: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Find unmatched entries between two CSVs by a key column.")
    p.add_argument("--alivlist", default=DEFAULT_ALIVLIST, help="Path to alivlist/master CSV (left)")
    p.add_argument("--core", default=DEFAULT_CORE, help="Path to core CSV (right), or 'wlist' to read from the database table via package_wlist")
    p.add_argument("--id-column", default="taxon_id", help="Key column name to compare on (default: taxon_id)")
    p.add_argument("--output-dir", default=None, help="Directory to write output CSVs")
    p.add_argument("--limit", type=int, default=20, help="Print at most this many sample IDs per side")

    args = p.parse_args(argv)

    try:
        left_index, left_fields = read_csv_indexed(args.alivlist, args.id_column)
        # For core, allow special value 'wlist' to indicate reading from DB table via package_wlist
        if str(args.core).lower() == "wlist":
            try:
                df_core = _pw.fetch_dataframe(_pw.CORE_QUERY)
            except Exception as db_e:
                print(f"Error fetching 'wlist' from DB: {db_e}", file=sys.stderr)
                return 2
            right_index, right_fields = df_indexed(df_core, args.id_column)
        else:
            right_index, right_fields = read_csv_indexed(args.core, args.id_column)
    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    left_ids: Set[str] = set(left_index.keys())
    right_ids: Set[str] = set(right_index.keys())

    only_in_left = sorted(list(left_ids - right_ids))
    only_in_right = sorted(list(right_ids - left_ids))
    in_both = left_ids & right_ids

    out_dir = ensure_output_dir(args.output_dir, args.alivlist, args.core)

    left_rows = [left_index[i] for i in only_in_left]
    right_rows = [right_index[i] for i in only_in_right]

    left_out = os.path.join(out_dir, "unmatched_in_alivlist_not_in_core.csv")
    right_out = os.path.join(out_dir, "unmatched_in_core_not_in_alivlist.csv")

    write_rows(left_out, left_rows, left_fields)
    write_rows(right_out, right_rows, right_fields)

    print("Comparison summary")
    print("-" * 72)
    print(f"Left (alivlist): {args.alivlist}")
    print(f"Right (core):    {args.core}")
    print(f"Key column:      {args.id_column}")
    print()
    print(f"Total IDs in left:  {len(left_ids):>6}")
    print(f"Total IDs in right: {len(right_ids):>6}")
    print(f"In both:            {len(in_both):>6}")
    print(f"Only in left:       {len(only_in_left):>6}")
    print(f"Only in right:      {len(only_in_right):>6}")
    print()
    def sample(lst: List[str]) -> List[str]:
        return lst[: max(0, args.limit)] if args.limit else lst

    if only_in_left:
        print(f"Sample IDs only in left (max {args.limit}): {', '.join(sample(only_in_left))}")
    if only_in_right:
        print(f"Sample IDs only in right (max {args.limit}): {', '.join(sample(only_in_right))}")
    print()
    print(f"Wrote: {left_out}")
    print(f"Wrote: {right_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
