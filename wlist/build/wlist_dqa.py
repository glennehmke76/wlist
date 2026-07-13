"""
wlist_dqa.py
Data Quality Assessment for the wlist dataset.
Outputs a Markdown report to wlist_dqa_report.md

Usage:
    python wlist_dqa.py [--host HOST] [--port PORT] [--dbname DBNAME]
                        [--user USER] [--password PASSWORD]
                        [--output OUTPUT]

Defaults to environment variables PGHOST, PGPORT, PGDATABASE, PGUSER,
PGPASSWORD if flags are not provided.
"""

import argparse
import os
import psycopg2
from datetime import datetime, timezone
import re


# ---------------------------------------------------------------------------
# CLI / connection helpers
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="wlist data quality assessment")
    # Prefer DCORE_* env vars used by package_wlist.py, fall back to PG* and then sane defaults
    p.add_argument("--host",     default=os.getenv("DCORE_HOST", os.getenv("PGHOST", "localhost")))
    p.add_argument("--port",     default=os.getenv("DCORE_PORT", os.getenv("PGPORT", "5432")))
    p.add_argument("--dbname",   default=os.getenv("DCORE_DB",  os.getenv("PGDATABASE", "dcoredb")))
    p.add_argument("--user",     default=os.getenv("DCORE_USER", os.getenv("PGUSER", "glennehmke")))
    # No hardcoded fallback (ecosystem D1 / wlist ADR-002): falls back to .pgpass if unset.
    p.add_argument("--password", default=os.getenv("DCORE_PASSWORD", os.getenv("PGPASSWORD", "")))
    p.add_argument("--output",   default="wlist_dqa_report.md",
                   help="Output Markdown file path")
    return p.parse_args()


def get_connection(args):
    # Only pass a password if one was explicitly provided. This allows libpq
    # to fall back to .pgpass, environment, or peer authentication when no
    # password is supplied. Additionally, align with package_wlist.py by
    # considering DCORE_PASSWORD/PGPASSWORD if args.password is empty.
    conn_kwargs = {
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
    }
    pwd = getattr(args, "password", None)
    if not pwd:
        # Pick up environment defaults used by package_wlist.py if available
        pwd = os.getenv("DCORE_PASSWORD") or os.getenv("PGPASSWORD")
    if pwd:  # do not pass empty string
        conn_kwargs["password"] = pwd
    return psycopg2.connect(**conn_kwargs)


def scalar(cur, sql, params=None):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# 1. Completeness (null rates)
# ---------------------------------------------------------------------------

NULLABLE_COLUMNS = [
    "sp_id",
    "taxon_level",
    "taxon_scientific_name",
    "family_name",
    "family_scientific_name",
    "t_order",
    "avibase_id",
    "bird_group",
    "population",
    "is_coastal",
    "aust_rli_1990",
    "aust_rli_2000",
    "aust_rli_2010",
    "aust_rli",
    "alist_change",
    "alist_change_note",
]


def assess_completeness(cur):
    total = scalar(cur, "SELECT COUNT(*) FROM wlist")
    rows = []
    for col in NULLABLE_COLUMNS:
        null_count = scalar(
            cur,
            f"SELECT COUNT(*) FROM wlist WHERE {col} IS NULL"
        )
        pct_complete = round(100.0 * (total - null_count) / total, 1) if total else 0.0
        rows.append((col, total, null_count, pct_complete))
    return total, rows


# ---------------------------------------------------------------------------
# 2. Referential integrity
# ---------------------------------------------------------------------------

def assess_referential_integrity(cur):
    orphaned = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM wlist w
        LEFT JOIN lut_rli r ON w.aust_rli = r.id
        WHERE w.aust_rli IS NOT NULL
          AND r.id IS NULL
        """
    )
    lut_count = scalar(cur, "SELECT COUNT(*) FROM lut_rli")
    return orphaned, lut_count


# ---------------------------------------------------------------------------
# 3. Constraint compliance
# ---------------------------------------------------------------------------

def assess_constraints(cur):
    invalid_coastal = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM wlist
        WHERE is_coastal IS NOT NULL
          AND NOT (is_coastal = ANY (ARRAY[1, 2]))
        """
    )
    invalid_alist = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM wlist
        WHERE alist_change IS NOT NULL
          AND alist_change NOT IN (0, 0.5, 1)
        """
    )
    return invalid_coastal, invalid_alist


# ---------------------------------------------------------------------------
# 4. Duplicate detection
# ---------------------------------------------------------------------------

def assess_duplicates(cur):
    dup_taxon_name = scalar(
        cur,
        """
        SELECT COUNT(*) FROM (
            SELECT taxon_name
            FROM wlist
            GROUP BY taxon_name
            HAVING COUNT(*) > 1
        ) t
        """
    )
    dup_scientific = scalar(
        cur,
        """
        SELECT COUNT(*) FROM (
            SELECT taxon_scientific_name
            FROM wlist
            WHERE taxon_scientific_name IS NOT NULL
            GROUP BY taxon_scientific_name
            HAVING COUNT(*) > 1
        ) t
        """
    )
    dup_taxon_id = scalar(
        cur,
        """
        SELECT COUNT(*) FROM (
            SELECT taxon_id
            FROM wlist
            GROUP BY taxon_id
            HAVING COUNT(*) > 1
        ) t
        """
    )
    dup_taxon_sort = scalar(
        cur,
        """
        SELECT COUNT(*) FROM (
            SELECT taxon_sort
            FROM wlist
            WHERE taxon_sort IS NOT NULL
            GROUP BY taxon_sort
            HAVING COUNT(*) > 1
        ) t
        """
    )
    return dup_taxon_name, dup_scientific, dup_taxon_id, dup_taxon_sort


# ---------------------------------------------------------------------------
# 5. AviBase ID and RLI coverage
# ---------------------------------------------------------------------------

def assess_coverage(cur):
    total = scalar(cur, "SELECT COUNT(*) FROM wlist")

    avibase_pop = scalar(
        cur, "SELECT COUNT(*) FROM wlist WHERE avibase_id IS NOT NULL"
    )

    # Rows missing AviBase identifiers (ordered for readability)
    cur.execute(
        """
        SELECT taxon_id,
               taxon_name,
               taxon_scientific_name AS taxon_sci,
               population
        FROM wlist
        WHERE avibase_id IS NULL
        ORDER BY taxon_sort
        """
    )
    avibase_missing_rows = cur.fetchall() or []

    rli_1990 = scalar(
        cur, "SELECT COUNT(*) FROM wlist WHERE aust_rli_1990 IS NOT NULL"
    )
    rli_2000 = scalar(
        cur, "SELECT COUNT(*) FROM wlist WHERE aust_rli_2000 IS NOT NULL"
    )
    rli_2010 = scalar(
        cur, "SELECT COUNT(*) FROM wlist WHERE aust_rli_2010 IS NOT NULL"
    )
    rli_current = scalar(
        cur, "SELECT COUNT(*) FROM wlist WHERE aust_rli IS NOT NULL"
    )

    # Taxa with no RLI assessment across any time period
    no_rli = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM wlist
        WHERE aust_rli_1990 IS NULL
          AND aust_rli_2000 IS NULL
          AND aust_rli_2010 IS NULL
          AND aust_rli     IS NULL
        """
    )

    # Rows where an Australian RLI is required but currently missing
    cur.execute(
        """
        SELECT taxon_id,
               taxon_name,
               taxon_scientific_name AS taxon_sci,
               population
        FROM wlist
        WHERE COALESCE(rli_required, 0) = 1
          AND aust_rli IS NULL
        ORDER BY taxon_sort
        """
    )
    aust_rli_missing_required_rows = cur.fetchall() or []

    def pct(n):
        return round(100.0 * n / total, 1) if total else 0.0

    return {
        "total": total,
        "avibase_populated": avibase_pop,
        "avibase_pct": pct(avibase_pop),
        "avibase_missing": len(avibase_missing_rows),
        "avibase_missing_rows": avibase_missing_rows,
        "rli_1990": rli_1990,   "rli_1990_pct": pct(rli_1990),
        "rli_2000": rli_2000,   "rli_2000_pct": pct(rli_2000),
        "rli_2010": rli_2010,   "rli_2010_pct": pct(rli_2010),
        "rli_current": rli_current, "rli_current_pct": pct(rli_current),
        "no_rli_any": no_rli,   "no_rli_pct": pct(no_rli),
        "aust_rli_missing_required": len(aust_rli_missing_required_rows),
        "aust_rli_missing_required_rows": aust_rli_missing_required_rows,
    }


# ---------------------------------------------------------------------------
# Report rendering helpers and DDL parsing
# ---------------------------------------------------------------------------

def pass_fail(condition):
    return "✅ PASS" if condition else "❌ FAIL"


def parse_schema_constraints_from_ddl():
    """Parse resources/sql/runtime/wlist_ddl.sql to extract a simple constraints catalog.

    Returns a list of dicts with keys: constraint, table, type, applies, purpose.
    The parsing is tailored to the repository's DDL format and constraint names.
    If the DDL file is not found or cannot be parsed, returns an empty list.
    """
    here = os.path.dirname(__file__)
    ddl_path = os.path.join(here, "..", "resources", "sql", "runtime", "wlist_ddl.sql")
    if not os.path.exists(ddl_path):
        return []

    constraints = []
    current_table = None
    purpose_by_name = {
        "wlist_pkey": "Ensures every taxon has a unique identifier",
        "wlist_taxon_name_ukey": "Ensures no two taxa share the same common name.",
        "wlist_taxon_scientific_name_ukey": "Ensures no two taxa share the same scientific name.",
        "wlist_aust_rli_fkey": "Ensures Red List values reference valid categories. Cascades on update; sets NULL on delete.",
        "wlist_coastal_range_check": "Only accepts valid coastal range codes.",
        "wlist_is_coastal_check": "Only accepts valid coastal codes: 1 (Obligate) or 2 (Facultative).",
        "wlist_alist_change_check": "Only accepts valid Avilist implementability values.",
        "wlist_ssp_ultrataxon_check": "Ensures every subspecies (ssp) row is flagged as an ultrataxon; subspecies cannot have is_ultrataxon NULL or FALSE.",
        "lut_rli_pkey": "Ensures each Red List category is uniquely identified",
        "lut_rli_code_ukey": "Ensures no duplication of short status codes.",
    }

    def add_constraint(line):
        # Expect lines like: CONSTRAINT name TYPE (cols) ...
        parts = line.strip().split()
        if len(parts) < 3 or parts[0] != "CONSTRAINT":
            return
        name = parts[1]
        ctype = parts[2]
        applies = ""
        # Try to extract column list within parentheses on this line
        open_paren = line.find("(")
        close_paren = line.find(")", open_paren + 1) if open_paren != -1 else -1
        if open_paren != -1 and close_paren != -1 and close_paren > open_paren:
            applies = line[open_paren + 1:close_paren].strip()
            # Normalize spaces
            applies = ", ".join([c.strip() for c in applies.split(",")])
        elif ctype == "CHECK":
            # For CHECK without simple columns, capture brief expression
            expr_start = line.find("CHECK (")
            if expr_start != -1:
                applies = line[expr_start + len("CHECK (") :].rstrip().rstrip(") ,")
        constraints.append({
            "constraint": name,
            "table": current_table or "",
            "type": ctype if ctype != "FOREIGN" else "FOREIGN KEY",
            "applies": applies,
            "purpose": purpose_by_name.get(name, ""),
        })

    with open(ddl_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.strip().startswith("CREATE TABLE "):
                # Example: CREATE TABLE wlist (
                try:
                    current_table = line.split()[2]
                except Exception:
                    current_table = None
                continue
            if line.strip().startswith("--"):
                continue
            if "CONSTRAINT" in line:
                add_constraint(line)

    return constraints


def fetch_db_constraints(cur):
    """Inspect the connected PostgreSQL database for constraints on tables
    in the public schema related to this project (e.g., wlist, lut_rli).

    Returns list of dicts: constraint, table, type, applies, purpose.
    """
    purpose_by_name = {
        # WLIST constraints (examples; extend as needed)
        "wlist_pkey": "Ensures every taxon has a unique identifier",
        "wlist_taxon_name_ukey": "Ensures no two taxa share the same common name.",
        "wlist_taxon_scientific_name_ukey": "Ensures no two taxa share the same scientific name.",
        "wlist_aust_rli_fkey": "Ensures Red List values reference valid categories. Cascades on update; sets NULL on delete.",
        "wlist_coastal_range_check": "Only accepts valid coastal range codes.",
        "wlist_is_coastal_check": "Only accepts valid coastal codes: 1 (Obligate) or 2 (Facultative).",
        "wlist_alist_change_check": "Only accepts valid Avilist implementability values.",
        # Constraint mentioned in the issue description
        "wlist_ssp_ultrataxon_taxonid_check": "Ensures subspecies rows (ssp) indicate ultrataxon consistency with taxon_id and flags.",
        "wlist_ssp_ultrataxon_check": "Ensures every subspecies (ssp) row is flagged as an ultrataxon; subspecies cannot have is_ultrataxon NULL or FALSE.",
        # LUT constraints
        "lut_rli_pkey": "Ensures each Red List category is uniquely identified",
        "lut_rli_code_ukey": "Ensures no duplication of short status codes.",
    }

    sql = """
        SELECT n.nspname AS schema,
               t.relname AS table_name,
               c.conname AS constraint_name,
               c.contype AS contype,
               pg_catalog.pg_get_constraintdef(c.oid, true) AS condef
        FROM pg_catalog.pg_constraint c
        JOIN pg_catalog.pg_class t ON t.oid = c.conrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
          AND t.relkind IN ('r','p')
          AND (t.relname LIKE 'wlist%' OR t.relname LIKE 'lut_rli%')
        ORDER BY t.relname, c.conname
    """
    cur.execute(sql)
    rows = cur.fetchall() or []

    type_map = {
        'p': 'PRIMARY KEY',
        'u': 'UNIQUE',
        'f': 'FOREIGN KEY',
        'c': 'CHECK',
        'x': 'EXCLUDE',
        't': 'TRIGGER',
    }

    results = []
    for _schema, table, name, contype, condef in rows:
        ctype = type_map.get(contype, contype)
        applies = ""
        if condef:
            s = " ".join(condef.split())
            m = re.search(r"\(([^()]*)\)", s)
            if m and ctype in ("PRIMARY KEY", "UNIQUE", "FOREIGN KEY"):
                applies = ", ".join([c.strip() for c in m.group(1).split(',') if c.strip()])
            elif ctype == "CHECK":
                expr = s.replace("CHECK ", "").strip()
                if len(expr) > 120:
                    expr = expr[:117] + "..."
                applies = expr
        results.append({
            "constraint": name,
            "table": table,
            "type": ctype,
            "applies": applies,
            "purpose": purpose_by_name.get(name, ""),
        })

    return results


def fetch_db_indexes(cur):
    """Return a list of index metadata dicts: index, table, type, column, purpose.
    Type is the access method (btree, gin, gist, hash, brin, etc.).
    Column is a comma-separated list extracted from indexdef.
    """
    purpose_by_name = {
        # Likely/known indexes
        "wlist_taxon_name_idx": "Speed lookups by common name.",
        "wlist_taxon_scientific_name_idx": "Speed lookups by scientific name.",
        "wlist_taxon_id_idx": "Ensure fast joins/filtering by taxon_id.",
        "wlist_taxon_sort_idx": "Support ordering by taxon_sort.",
        "wlist_avibase_id_idx": "Speed lookups by AviBase ID.",
        "wlist_aust_rli_idx": "Speed joins to lut_rli and filtering by RLI.",
        "lut_rli_code_idx": "Fast lookups by short Red List code.",
    }

    sql = """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND (tablename LIKE 'wlist%' OR tablename LIKE 'lut_rli%')
        ORDER BY tablename, indexname
    """
    cur.execute(sql)
    rows = cur.fetchall() or []

    def parse_type_and_cols(indexdef):
        itype = ""
        cols = ""
        if not indexdef:
            return itype, cols
        s = " ".join(indexdef.split())
        m = re.search(r"USING\s+(\w+)", s, re.IGNORECASE)
        if m:
            itype = m.group(1).lower()
        m2 = re.search(r"\(([^()]+)\)", s)
        if m2:
            cols = ", ".join([c.strip() for c in m2.group(1).split(',') if c.strip()])
        return itype, cols

    results = []
    for _schema, table, index, indexdef in rows:
        itype, cols = parse_type_and_cols(indexdef)
        results.append({
            "index": index,
            "table": table,
            "type": itype,
            "column": cols,
            "purpose": purpose_by_name.get(index, ""),
        })

    return results


def fetch_db_routines(cur):
    """Fetch functions and procedures in the public schema relevant to this project.

    Returns a list of dicts: name, type (FUNCTION/PROCEDURE), args, returns, language, purpose.
    """
    purpose_by_name = {
        # From issue description
        "update_ssp_required": "Trigger function to maintain ssp_required across sibling rows.",
        "update_is_core": "Trigger function to set is_core based on population value.",
        "wlist_add_row": "Procedure to insert a row into wlist and shift taxon_sort values below.",
        "wlist_delete_row": "Procedure to delete a row from wlist and close the taxon_sort gap.",
    }

    sql = """
        SELECT DISTINCT p.proname,
               p.prokind,                             -- 'f' function, 'p' procedure, 'a' aggregate, 'w' window
               pg_get_function_identity_arguments(p.oid) AS args,
               pg_get_function_result(p.oid)           AS returns,
               l.lanname                               AS language
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_language  l ON l.oid = p.prolang
        LEFT JOIN pg_trigger t ON t.tgfoid = p.oid AND NOT t.tgisinternal
        LEFT JOIN pg_class    c ON c.oid = t.tgrelid
        LEFT JOIN pg_namespace nt ON nt.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND p.prokind IN ('f','p')
          AND (
                p.proname LIKE 'wlist%'
             OR (t.oid IS NOT NULL AND nt.nspname = 'public' AND c.relname LIKE 'wlist%')
          )
        ORDER BY p.proname
    """
    cur.execute(sql)
    rows = cur.fetchall() or []

    kind_map = { 'f': 'FUNCTION', 'p': 'PROCEDURE', 'a': 'AGGREGATE', 'w': 'WINDOW' }

    results = []
    for name, prokind, args, returns, lang in rows:
        results.append({
            "name": name,
            "type": kind_map.get(prokind, prokind),
            "args": args or "",
            "returns": returns or "",
            "language": lang,
            "purpose": purpose_by_name.get(name, ""),
        })
    return results


def fetch_db_triggers(cur):
    """Fetch table triggers in the public schema and link them to functions/procedures.

    Returns list of dicts: trigger, table, timing, events, level, function, enabled, purpose.
    """
    purpose_by_name = {
        "trg_update_ssp_required": "Keeps ssp_required in sync when is_ultrataxon/taxon_level/sp_id change or rows are added/removed.",
        "trg_update_is_core": "Maintains is_core flag when population changes or a row is inserted.",
    }

    sql = """
        SELECT t.tgname AS trigger_name,
               c.relname AS table_name,
               pg_get_triggerdef(t.oid, true) AS trigger_def,
               t.tgenabled
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND NOT t.tgisinternal
          AND c.relname = 'wlist'
        ORDER BY c.relname, t.tgname
    """
    cur.execute(sql)
    rows = cur.fetchall() or []

    def parse_trigger(defn: str):
        # Example: CREATE TRIGGER trg ... BEFORE INSERT OR UPDATE OF population ON wlist FOR EACH ROW EXECUTE FUNCTION update_is_core()
        s = " ".join((defn or "").split())
        timing = ""
        events = ""
        level = ""
        func = ""
        when_cond = ""
        m = re.search(r"\b(BEFORE|AFTER|INSTEAD OF)\b", s)
        if m:
            timing = m.group(1).title()
        # Extract events between timing and ON
        m = re.search(r"\b(BEFORE|AFTER|INSTEAD OF)\b\s+(.+?)\s+ON\b", s)
        if m:
            events = m.group(2)
        m = re.search(r"\bFOR EACH\s+(ROW|STATEMENT)\b", s)
        if m:
            level = m.group(1).title()
        m = re.search(r"EXECUTE\s+(?:FUNCTION|PROCEDURE)\s+([^(\s]+)", s, re.IGNORECASE)
        if m:
            func = m.group(1)
        m = re.search(r"WHEN\s*\((.+)\)\s*EXECUTE", s)
        if m:
            when_cond = m.group(1)
        return timing, events, level, func, when_cond

    results = []
    for trg_name, table, trgdef, enabled in rows:
        timing, events, level, func, when_cond = parse_trigger(trgdef or "")
        results.append({
            "trigger": trg_name,
            "table": table,
            "timing": timing,
            "events": events,
            "level": level,
            "function": func,
            "enabled": enabled,
            "when": when_cond,
            "purpose": purpose_by_name.get(trg_name, ""),
        })

    return results


def render_report(total, completeness_rows, ref_int, constraints,
                  duplicates, coverage, db_info, schema_constraints=None,
                  db_constraints=None, db_indexes=None, db_routines=None, db_triggers=None):
    orphaned, lut_count = ref_int
    invalid_coastal, invalid_alist = constraints
    dup_taxon_name, dup_scientific, dup_taxon_id, dup_taxon_sort = duplicates

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    a = lines.append

    a("# wlist – Data Quality Assessment Report")
    a("")
    a(f"**Generated:** {ts}  ")
    a(f"**Database:** {db_info}  ")
    a(f"**Total taxa assessed:** {total:,}")
    a("")

    # ── Summary table ────────────────────────────────────────────────────────
    a("## 1. Summary")
    a("")
    a("| Assessment | Result | Status |")
    a("|---|---|---|")

    a(f"| Referential integrity | {orphaned} orphaned aust_rli value(s) | "
      f"{pass_fail(orphaned == 0)} |")

    a(f"| Constraint compliance – is_coastal | {invalid_coastal} invalid value(s) | "
      f"{pass_fail(invalid_coastal == 0)} |")

    a(f"| Constraint compliance – alist_change | {invalid_alist} invalid value(s) | "
      f"{pass_fail(invalid_alist == 0)} |")

    a(f"| Duplicate taxon names | {dup_taxon_name} duplicate(s) | "
      f"{pass_fail(dup_taxon_name == 0)} |")

    a(f"| Duplicate scientific names | {dup_scientific} duplicate(s) | "
      f"{pass_fail(dup_scientific == 0)} |")

    a(f"| Duplicate taxon_id values | {dup_taxon_id} duplicate(s) | "
      f"{pass_fail(dup_taxon_id == 0)} |")

    a(f"| Duplicate taxon_sort values | {dup_taxon_sort} duplicate(s) | "
      f"{pass_fail(dup_taxon_sort == 0)} |")

    a(f"| AviBase ID coverage | {coverage['avibase_pct']}% populated | "
      f"{'✅ PASS' if coverage['avibase_pct'] == 100 else '⚠️ PARTIAL'} |")

    a(f"| RLI coverage (current) | {coverage['rli_current_pct']}% populated | "
      f"{'✅ PASS' if coverage['rli_current_pct'] == 100 else '⚠️ PARTIAL'} |")

    a("")

    # ── Constraints ──────────────────────────────────────────────────────────
    a("## 2. Constraints")
    a("")
    a("| Constraint | Table | Type | Applies to | Purpose |")
    a("|---|---|---|---|---|")
    if db_constraints:
        for c in db_constraints:
            a(f"| {c['constraint']} | {c['table']} | {c['type']} | {c.get('applies','')} | {c.get('purpose','')} |")
    else:
        a("| (none found) | | | | |")
    a("")

    # ── Indexes ───────────────────────────────────────────────────────────────
    a("## 3. Indexes")
    a("")
    a("| Index | Table | Type | Column | Purpose |")
    a("|---|---|---|---|---|")
    if db_indexes:
        for ix in db_indexes:
            a(f"| {ix['index']} | {ix['table']} | {ix['type']} | {ix.get('column','')} | {ix.get('purpose','')} |")
    else:
        a("| (none found) | | | | |")
    a("")

    # ── 1. Referential integrity ─────────────────────────────────────────────
    a("## 4. Referential Integrity")
    a("")
    a(f"**lut_rli** contains {lut_count} category entries.  ")
    a(f"**wlist.aust_rli → lut_rli.id:** {orphaned} orphaned value(s).  ")
    a("")
    if orphaned == 0:
        a("> All `aust_rli` values resolve correctly to a `lut_rli` entry.")
    else:
        a(f"> ❌ {orphaned} row(s) in `wlist` have an `aust_rli` value with no "
          f"matching entry in `lut_rli`. These rows will fail foreign key "
          f"enforcement and should be investigated.")
    a("")

    # ── 2. Constraint compliance ─────────────────────────────────────────────
    a("## 5. Constraint Compliance")
    a("")
    a("| Constraint | Allowed values | Violations |")
    a("|---|---|---|")
    a(f"| is_coastal | 1, 2 | {invalid_coastal} |")
    a(f"| alist_change | 0, 0.5, 1 | {invalid_alist} |")
    a("")
    if invalid_coastal == 0 and invalid_alist == 0:
        a("> All values satisfy their check constraints.")
    else:
        a("> ❌ Constraint violations detected. Review affected rows before publication.")
    a("")

    # ── 3. Duplicate detection ───────────────────────────────────────────────
    # -- New sections: Functions/Procedures and Triggers (from issue requirements)
    a("## 6. Functions and Procedures")
    a("")
    a("| Name | Type | Arguments | Returns | Language | Purpose |")
    a("|---|---|---|---|---|---|")
    if db_routines:
        for r in db_routines:
            a(f"| {r['name']} | {r['type']} | {r.get('args','')} | {r.get('returns','')} | {r.get('language','')} | {r.get('purpose','')} |")
    else:
        a("| (none found) | | | | | |")
    a("")

    a("## 7. Triggers")
    a("")
    a("| Trigger | Table | Timing | Events | Level | Function | Enabled | Purpose |")
    a("|---|---|---|---|---|---|---|---|")
    if db_triggers:
        for t in db_triggers:
            a(f"| {t['trigger']} | {t['table']} | {t.get('timing','')} | {t.get('events','')} | {t.get('level','')} | {t.get('function','')} | {t.get('enabled','')} | {t.get('purpose','')} |")
    else:
        a("| (none found) | | | | | | | |")
    a("")
    a("> Where triggers exist, the linked function/procedure column indicates the database routine invoked by the trigger.")
    a("")

    a("## 8. Duplicate Detection")
    a("")
    a("| Field | Duplicate groups |")
    a("|---|---|")
    a(f"| taxon_name | {dup_taxon_name} |")
    a(f"| taxon_scientific_name | {dup_scientific} |")
    a(f"| taxon_id | {dup_taxon_id} |")
    a(f"| taxon_sort | {dup_taxon_sort} |")
    a("")
    if (dup_taxon_name == 0 and dup_scientific == 0 and
            dup_taxon_id == 0 and dup_taxon_sort == 0):
        a("> No duplicate names or identifiers detected.")
    else:
        a("> ⚠️ Duplicate values detected. Note that some name duplication may be "
          "expected where the same name applies to multiple ultrataxa (e.g. "
          "nominate subspecies sharing a vernacular name with the species). "
          "Review to confirm whether duplicates are intentional.")
    a("")

    # ── 4. Coverage ──────────────────────────────────────────────────────────
    a("## 9. AviBase ID and RLI Coverage")
    a("")
    a("### AviBase identifier")
    a("")
    a(f"| Metric | Count | Coverage |")
    a("|---|---|---|")
    a(f"| AviBase ID populated | {coverage['avibase_populated']:,} "
      f"| {coverage['avibase_pct']}% |")
    a("")

    # Missing AviBase identifiers table
    a("#### Missing AviBase identifiers")
    a("")
    a("| taxon_id | taxon_name | taxon_sci | population |")
    a("|---|---|---|---|")
    rows = coverage.get('avibase_missing_rows') or []
    if rows:
        for taxon_id, taxon_name, taxon_sci, population in rows:
            taxon_sci = taxon_sci if taxon_sci is not None else ""
            population = population if population is not None else ""
            a(f"| {taxon_id} | {taxon_name} | {taxon_sci} | {population} |")
    else:
        a("| (none) | | | |")
    a("")
    a("> Orphans are due to global list differences and are expected")
    a("")

    a("### Australian Red List Index – coverage by time period")
    a("")
    a("| Period | Taxa assessed | Coverage |")
    a("|---|---|---|")
    a(f"| 1990 | {coverage['rli_1990']:,} | {coverage['rli_1990_pct']}% |")
    a(f"| 2000 | {coverage['rli_2000']:,} | {coverage['rli_2000_pct']}% |")
    a(f"| 2010 | {coverage['rli_2010']:,} | {coverage['rli_2010_pct']}% |")
    a(f"| Current | {coverage['rli_current']:,} | {coverage['rli_current_pct']}% |")
    a(f"| No assessment (any period) | {coverage['no_rli_any']:,} "
      f"| {coverage['no_rli_pct']}% of all taxa |")
    a("")
    a("> Taxa with no RLI assessment across any time period may include "
      "recently described taxa, data-deficient taxa, or ultrataxa outside "
      "the scope of formal assessment cycles.")
    a("")

    # Missing Australian RLI for required taxa (rli_required = 1)
    a("#### Missing Australian RLI (required taxa)")
    a("")
    a("| taxon_id | taxon_name | taxon_sci | population |")
    a("|---|---|---|---|")
    req_rows = coverage.get('aust_rli_missing_required_rows') or []
    if req_rows:
        for taxon_id, taxon_name, taxon_sci, population in req_rows:
            taxon_sci = taxon_sci if taxon_sci is not None else ""
            population = population if population is not None else ""
            a(f"| {taxon_id} | {taxon_name} | {taxon_sci} | {population} |")
    else:
        a("| (none) | | | |")
    a("")

    # ── Notes ────────────────────────────────────────────────────────────────
    a("## 10. Notes")
    a("")
    a("- This assessment focuses on structural and relational quality. It does not "
      "validate scientific names against external taxonomic authorities (e.g. "
      "AviList, AviBase).")
    a("- Duplicate name detection flags groups for review; some duplication "
      "between species and nominate subspecies records is by design.")
    a("- RLI coverage below 100% for historical periods (1990, 2000, 2010) "
      "is expected where taxa were not formally assessed in those cycles.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    conn = get_connection(args)
    cur = conn.cursor()

    db_info = f"{args.dbname} @ {args.host}:{args.port}"

    total, completeness_rows = assess_completeness(cur)
    ref_int   = assess_referential_integrity(cur)
    constraints = assess_constraints(cur)
    duplicates  = assess_duplicates(cur)
    coverage    = assess_coverage(cur)

    # Parse schema constraints from repository DDL for inclusion in the report
    schema_constraints = parse_schema_constraints_from_ddl()
    # Sort for stable, readable output
    schema_constraints = sorted(
        schema_constraints,
        key=lambda d: (d.get('table',''), d.get('constraint',''))
    )

    # Introspect constraints and indexes from the live database
    try:
        db_constraints = fetch_db_constraints(cur)
    except Exception as e:
        db_constraints = []
        print(f"Warning: Could not fetch DB constraints: {e}")

    try:
        db_indexes = fetch_db_indexes(cur)
    except Exception as e:
        db_indexes = []
        print(f"Warning: Could not fetch DB indexes: {e}")

    try:
        db_routines = fetch_db_routines(cur)
    except Exception as e:
        db_routines = []
        print(f"Warning: Could not fetch DB routines: {e}")

    try:
        db_triggers = fetch_db_triggers(cur)
    except Exception as e:
        db_triggers = []
        print(f"Warning: Could not fetch DB triggers: {e}")

    report = render_report(
        total, completeness_rows, ref_int,
        constraints, duplicates, coverage, db_info, schema_constraints,
        db_constraints=db_constraints, db_indexes=db_indexes,
        db_routines=db_routines, db_triggers=db_triggers
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to: {args.output}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
