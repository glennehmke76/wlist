#%%
"""
Package and export wlist data to CSVs and an SQL dump (with CREATE TABLE + INSERTs, no indexes/keys).

- Output directory (absolute): /Users/glennehmke/MEGA/Taxonomy/wlist/package
- CSV format: UTF-8 with text cells quoted (numbers unquoted)
- SQL dump: includes CREATE TABLE statements (with PK for wlist) and INSERT rows.

Database connection uses environment variables when available, with sane defaults:
  DCORE_HOST, DCORE_DB, DCORE_USER, DCORE_PASSWORD, DCORE_PORT

This script can be run as a regular Python file.
"""
#%%
import os
import sys
import csv
import math
import re
from typing import Dict, Tuple

import shutil
import subprocess
import psycopg2
import pandas as pd
from types import SimpleNamespace

# Try package and script import styles for wlist_dqa
try:
    from . import wlist_dqa as wlist_dqa
except Exception:  # pragma: no cover
    import wlist_dqa as wlist_dqa

#%%
OUTPUT_DIR = "/Users/glennehmke/MEGA/Taxonomy/wlist/package"
CORE_CSV = os.path.join(OUTPUT_DIR, "wlist_core.csv")
RLI_CSV = os.path.join(OUTPUT_DIR, "lut_rli.csv")
AVILIST_CHANGES_CSV = os.path.join(OUTPUT_DIR, "avilist_changes.csv")
SQL_DUMP = os.path.join(OUTPUT_DIR, "wlist_core.sql")
DDL_EXPORT = os.path.join(OUTPUT_DIR, "wlist.ddl")
DQA_REPORT = os.path.join(OUTPUT_DIR, "wlist_dqa_report.md")

#%%
def get_db_connection():
    host = os.getenv("DCORE_HOST", "localhost")
    dbname = os.getenv("DCORE_DB", "dcoredb")
    user = os.getenv("DCORE_USER", "glennehmke")
    # No hardcoded fallback (ecosystem D1 / wlist ADR-002): if DCORE_PASSWORD isn't
    # set, password=None lets psycopg2 fall back to ~/.pgpass.
    password = os.getenv("DCORE_PASSWORD")
    port = int(os.getenv("DCORE_PORT", "5432"))
    return psycopg2.connect(host=host, dbname=dbname, user=user, password=password, port=port)

#%%
# Queries from issue description
CORE_QUERY = (
    """
    SELECT
      wlist.taxon_sort,
      wlist.is_ultrataxon,
      wlist.taxon_level,
      wlist.sp_id,
      wlist.taxon_id,
      wlist.taxon_name,
      wlist.taxon_scientific_name,
      wlist.family_name,
      wlist.family_scientific_name,
      wlist.t_order AS order,
      wlist.avibase_id,
      wlist.notes,
      wlist.bird_group,
      wlist.population,
      CASE
        WHEN wlist.is_coastal = 1 THEN 'Obligate'
        WHEN wlist.is_coastal = 2 THEN 'Facultative'
      ELSE NULL END AS is_coastal,
      wlist.aust_rli_1990,
      wlist.aust_rli_2000,
      wlist.aust_rli_2010,
      wlist.aust_rli,
      rl.category AS aust_rli_status_desc
    FROM wlist
    LEFT JOIN lut_rli rl ON wlist.aust_rli = rl.id
    ORDER BY wlist.taxon_sort
    ;
    """
)

RLI_QUERY = (
    """
    SELECT
      lut_rli.id,
      lut_rli.code,
      lut_rli.category
    FROM lut_rli;
    """
)

AVILIST_CHANGES_QUERY = (
    """
    SELECT
      wlist.taxon_id,
      CASE
        WHEN wlist.alist_change = 1 THEN 'Implementable'
        WHEN wlist.alist_change = 0 THEN 'Not implementable'
        WHEN wlist.alist_change = 0.5 THEN 'Partially implementable'
        ELSE NULL END AS alist_change,
      wlist.alist_change_note
    FROM wlist
    WHERE
      wlist.alist_change IS NOT NULL
    ORDER BY wlist.taxon_sort
    ;
    """
)

#%%
def fetch_dataframe(sql: str) -> pd.DataFrame:
    with get_db_connection() as conn:
        df = pd.read_sql(sql, conn)
    return df

#%%
def _to_camel_case(name: str) -> str:
    import re
    parts = re.split(r'[^A-Za-z0-9]+', name.strip())
    parts = [p for p in parts if p != ""]
    if not parts:
        return name
    first = parts[0].lower()
    rest = [p[:1].upper() + p[1:] if p else "" for p in parts[1:]]
    return first + "".join(rest)


def export_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Convert column names to camelCase for CSV export only
    df_out = df.copy()
    df_out.columns = [_to_camel_case(str(c)) for c in df_out.columns]
    # Ensure UTF-8 and quote text cells only (non-numeric).
    # Pandas to_csv doesn't have QUOTE_NONNUMERIC directly, so we use csv module's constant via 'quoting'.
    df_out.to_csv(path, index=False, encoding="utf-8", quoting=csv.QUOTE_NONNUMERIC)

#%%
# Simple dtype mapping from pandas to generic SQL types (PostgreSQL-flavored, but generic enough)
PANDAS_DTYPE_TO_SQL = {
    "int64": "BIGINT",
    "Int64": "BIGINT",
    "int32": "INTEGER",
    "Int32": "INTEGER",
    "float64": "DOUBLE PRECISION",
    "Float64": "DOUBLE PRECISION",
    "bool": "BOOLEAN",
    "boolean": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
    "object": "TEXT",
    "string": "TEXT",
}

# Handle pandas NA for different dtypes
def is_na(value) -> bool:
    if value is None:
        return True
    # pandas NA/NaT
    try:
        import pandas as _pd
        if value is _pd.NA:
            return True
    except Exception:
        pass
    # NaN
    if isinstance(value, float) and math.isnan(value):
        return True
    return False

# SQL literal escaping for text
def sql_escape_text(value: str) -> str:
    return value.replace("'", "''")

# Render a single cell as SQL literal based on dtype
def to_sql_literal(value, dtype: str) -> str:
    if is_na(value):
        return "NULL"
    base = str(dtype)
    if base.startswith("int") or base.startswith("Int"):
        return str(int(value))
    if base.startswith("float") or base.startswith("Float"):
        # Preserve as-is; avoid scientific by using repr then cast
        return ("%r" % float(value))
    if base in ("bool", "boolean"):
        return "TRUE" if bool(value) else "FALSE"
    if "datetime" in base:
        return f"'{sql_escape_text(pd.to_datetime(value).strftime('%Y-%m-%d %H:%M:%S'))}'"
    # default: treat as text
    return f"'{sql_escape_text(str(value))}'"

#%%
def infer_sql_type(series: pd.Series) -> str:
    dtype_name = str(series.dtype)
    return PANDAS_DTYPE_TO_SQL.get(dtype_name, "TEXT")

# Identifier helpers
_defq = '"'

def _quote_ident(ident: str) -> str:
    return _defq + ident.replace('"', '""') + _defq

def format_table_identifier(table_name: str) -> str:
    if "." in table_name:
        schema, table = table_name.split(".", 1)
        return f"{_quote_ident(schema)}.{_quote_ident(table)}"
    return _quote_ident(table_name)

#%%
def generate_create_table_sql(table_name: str, df: pd.DataFrame) -> str:
    cols = []
    for col in df.columns:
        col_dtype = infer_sql_type(df[col])
        cols.append(f'  {_quote_ident(col)} {col_dtype}')
    cols_sql = ",\n".join(cols)
    return f"CREATE TABLE IF NOT EXISTS {format_table_identifier(table_name)} (\n{cols_sql}\n);\n\n"

# Fixed DDL for public.wlist per specification
WLIST_DDL = (
    "CREATE TABLE public.wlist\n"
    "(\n"
    "    taxon_sort                  integer,\n"
    "    is_ultrataxon               smallint,\n"
    "    taxon_level                 varchar(50),\n"
    "    sp_id                       smallint,\n"
    "    taxon_id                    varchar(20) not null\n"
    "        constraint wlist_pk\n"
    "            primary key,\n"
    "    taxon_name                  varchar(255),\n"
    "    taxon_scientific_name       varchar(255),\n"
    "    family_name                 varchar(255),\n"
    "    family_scientific_name      varchar(255),\n"
    "    \"order\"                  varchar(255),\n"
    "    avibase_id                  varchar(255) default NULL::character varying,\n"
    "    notes                       text,\n"
    "    bird_group                  varchar(255),\n"
    "    population                  varchar(255),\n"
    "    is_coastal                  varchar(255),\n"
    "    aust_rli_1990               smallint,\n"
    "    aust_rli_2000               smallint,\n"
    "    aust_rli_2010               smallint,\n"
    "    aust_rli                    smallint,\n"
    "    aust_rli_status_desc        varchar(255)\n"
    ");\n\n"
)

# Columns present in the fixed WLIST_DDL (used to filter constraints/indexes)
CORE_WLIST_COLUMNS = [
    "taxon_sort",
    "is_ultrataxon",
    "taxon_level",
    "sp_id",
    "taxon_id",
    "taxon_name",
    "taxon_scientific_name",
    "family_name",
    "family_scientific_name",
    "order",
    "avibase_id",
    "notes",
    "bird_group",
    "population",
    "is_coastal",
    "aust_rli_1990",
    "aust_rli_2000",
    "aust_rli_2010",
    "aust_rli",
    "aust_rli_status_desc",
]

#%%
def generate_insert_sql(table_name: str, df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    lines = []
    col_list = ", ".join([_quote_ident(c) for c in df.columns])
    for _, row in df.iterrows():
        values = [to_sql_literal(row[c], str(df[c].dtype)) for c in df.columns]
        values_sql = ", ".join(values)
        lines.append(f"INSERT INTO {format_table_identifier(table_name)} ({col_list}) VALUES ({values_sql});")
    return "\n".join(lines) + "\n\n"

#%%
def export_sql_dump(tables: Dict[str, pd.DataFrame], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    parts = [
        "-- wlist export (tables only; wlist includes PK)\n",
        "SET client_encoding = 'UTF8';\n\n",
    ]
    for table_name, df in tables.items():
        if table_name == "public.wlist":
            parts.append(WLIST_DDL)
        else:
            parts.append(generate_create_table_sql(table_name, df))
        parts.append(generate_insert_sql(table_name, df))
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(parts)

#%%
# Export the repository-checked-in DDL as wlist.ddl to the OUTPUT_DIR

def export_schema_ddl(dest_path: str) -> None:
    """
    Create wlist.ddl directly and exclusively from the live database connection.

    - Connects using get_db_connection() (DCORE_* envs used for credentials).
    - Introspects columns, constraints, indexes, and comments for public.wlist and public.lut_rli.
    - Writes a DDL file formatted similarly to the repository's wlist_ddl.sql with
      section headers, DROP TABLE, CREATE TABLE, ALTER ADD CONSTRAINT, indexes, and comments.
    - No file-based fallback is performed; if the database is unavailable or tables are
      missing, an exception is raised to the caller.
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    def qident(name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    def fmt_fullname(table: str) -> str:
        return f"public.{table}"

    def fmt_type(row: dict) -> str:
        dt = row.get("data_type", "")
        udt = row.get("udt_name", "")
        charlen = row.get("character_maximum_length")
        prec = row.get("numeric_precision")
        scale = row.get("numeric_scale")
        if dt in ("character varying", "varchar"):
            return f"varchar({charlen})" if charlen else "varchar"
        if dt in ("character", "char"):
            return f"char({charlen})" if charlen else "char"
        if dt == "numeric":
            if prec is not None and scale is not None:
                return f"numeric({int(prec)},{int(scale)})"
            if prec is not None:
                return f"numeric({int(prec)})"
            return "numeric"
        if dt == "timestamp without time zone":
            return "timestamp without time zone"
        if dt == "timestamp with time zone":
            return "timestamp with time zone"
        if dt in ("double precision", "real", "integer", "bigint", "smallint", "boolean", "text"):
            return dt
        # Fallback to underlying type name
        return udt or dt or "text"

    def esc_literal(txt: str) -> str:
        return txt.replace("'", "''")

    def fetch_table_columns(cur, table: str):
        sql = """
            SELECT ordinal_position, column_name, is_nullable, data_type,
                   character_maximum_length, numeric_precision, numeric_scale,
                   datetime_precision, udt_name, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """
        cur.execute(sql, (table,))
        cols = []
        for (ordpos, name, is_null, data_type, charlen, prec, scale, dtprec, udt, default) in cur.fetchall() or []:
            cols.append({
                "ordinal_position": ordpos,
                "column_name": name,
                "is_nullable": is_null,
                "data_type": data_type,
                "character_maximum_length": charlen,
                "numeric_precision": prec,
                "numeric_scale": scale,
                "datetime_precision": dtprec,
                "udt_name": udt,
                "column_default": default,
            })
        return cols

    def fetch_constraints(cur, table: str):
        sql = """
            SELECT c.conname, c.contype, pg_get_constraintdef(c.oid, true) AS condef
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public' AND t.relname = %s
            ORDER BY c.conname
        """
        cur.execute(sql, (table,))
        return cur.fetchall() or []  # list of (conname, contype, condef)

    def fetch_indexes(cur, table: str):
        sql = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = %s
            ORDER BY indexname
        """
        cur.execute(sql, (table,))
        return cur.fetchall() or []  # list of (indexname, indexdef)

    def fetch_table_comment(cur, table: str):
        sql = """
            SELECT obj_description(t.oid, 'pg_class')
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public' AND t.relname = %s
        """
        cur.execute(sql, (table,))
        row = cur.fetchone()
        return row[0] if row and row[0] else None

    def fetch_column_comments(cur, table: str):
        sql = """
            SELECT a.attname, d.description
            FROM pg_class t
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum > 0 AND NOT a.attisdropped
            LEFT JOIN pg_description d ON d.objoid = t.oid AND d.objsubid = a.attnum
            WHERE n.nspname = 'public' AND t.relname = %s AND d.description IS NOT NULL
            ORDER BY a.attnum
        """
        cur.execute(sql, (table,))
        return cur.fetchall() or []  # list of (column, description)

    def build_create_table(table: str, columns: list) -> str:
        lines = []
        for col in columns:
            coltype = fmt_type(col)
            parts = [f"  {qident(col['column_name'])} {coltype}"]
            if col.get("column_default"):
                parts.append(f"DEFAULT {col['column_default']}")
            if (col.get("is_nullable") or "").upper() == "NO":
                parts.append("NOT NULL")
            lines.append(" ".join(parts))
        inner = ",\n".join(lines)
        return f"CREATE TABLE {fmt_fullname(table)}\n(\n{inner}\n);\n"

    def write_table_section(out, table: str, cur):
        # If limiting to core fields for main table, emit fixed CREATE TABLE for wlist
        if table == "wlist":
            # Header and DROP
            out.write("-- =============================================================================\n")
            out.write("-- TABLE: wlist (parent table)\n")
            out.write("-- =============================================================================\n")
            out.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
            # Emit fixed core-field DDL (kept in-sync with CORE_QUERY/WLIST_DDL)
            out.write(WLIST_DDL)

            # Re-include constraints, indexes, and checks from live DB, filtered to core columns
            # Fetch live metadata
            live_columns = fetch_table_columns(cur, table)
            live_col_names = {c["column_name"] for c in live_columns}
            cons = fetch_constraints(cur, table)
            idxs = fetch_indexes(cur, table)
            tbl_comment = fetch_table_comment(cur, table)
            col_comments = fetch_column_comments(cur, table)

            core_set = set(CORE_WLIST_COLUMNS)

            def _extract_cols_from_def(defn: str) -> list:
                if not defn:
                    return []
                s = " ".join(defn.split())
                # Grab first parenthesized list (works for PK/UNIQUE/FOREIGN local cols)
                m = re.search(r"\(([^()]*)\)", s)
                if not m:
                    return []
                raw = m.group(1)
                cols = []
                for part in raw.split(','):
                    p = part.strip().strip('"')
                    cols.append(p)
                return cols
            
            # Map of PK/UNIQUE constraint names to exclude their implicit indexes
            pk_uk_names = {name for (name, contype, _def) in cons if contype in ("p", "u")}

            # Constraints: include if referenced columns are subset of CORE_WLIST_COLUMNS
            for (name, ctype, condef) in cons:
                ref_cols = _extract_cols_from_def(condef)
                if ctype in ("p", "u", "f"):
                    if ref_cols and all((c.strip('"') in core_set) for c in ref_cols):
                        out.write(f"ALTER TABLE ONLY {fmt_fullname(table)} ADD CONSTRAINT {name} {condef};\n")
                elif ctype == "c":  # CHECK
                    # Heuristic: find identifiers that are live column names; require all to be in core
                    idents = set()
                    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", condef or ""):
                        if tok in live_col_names:
                            idents.add(tok)
                    if idents.issubset(core_set):
                        out.write(f"ALTER TABLE ONLY {fmt_fullname(table)} ADD CONSTRAINT {name} {condef};\n")
                else:
                    # Other constraint types are not expected; skip
                    pass

            # Indexes: exclude those backing PK/UNIQUE and include only if columns are subset of core
            def _index_cols(indexdef: str) -> list:
                if not indexdef:
                    return []
                s = " ".join(indexdef.split())
                m = re.search(r"\(([^()]+)\)", s)
                if not m:
                    return []
                raw = m.group(1)
                cols = []
                for part in raw.split(','):
                    p = part.strip()
                    # Handle expressions like LOWER(col) by extracting bare identifier if quoted or plain
                    mcol = re.search(r'"([^"]+)"', p)
                    if mcol:
                        cols.append(mcol.group(1))
                    else:
                        # take first token up to space or '(' to approximate column name
                        base = re.split(r"[\s(]", p)[0]
                        cols.append(base.strip().strip('"'))
                return cols

            real_indexes = [(iname, idef) for (iname, idef) in idxs if iname not in pk_uk_names]
            kept_indexes = []
            for (iname, idef) in real_indexes:
                cols = _index_cols(idef)
                # If no columns detected (expression index), keep only if expressions reference core columns heuristically
                if cols:
                    if all(c in core_set for c in cols):
                        kept_indexes.append((iname, idef))
                else:
                    # Heuristic: allow expression indexes only if any core column name appears
                    if any(cc in (idef or "") for cc in core_set):
                        kept_indexes.append((iname, idef))

            if kept_indexes:
                out.write("\n-- Indexes for wlist\n")
                for (_iname, idef) in kept_indexes:
                    out.write(idef.rstrip("\n") + "\n")

            # Comments limited to core columns
            if tbl_comment:
                out.write("\n-- Table comments\n")
                out.write(f"COMMENT ON TABLE {fmt_fullname(table)} IS '{esc_literal(tbl_comment)}';\n")
            core_comments = [(c, d) for (c, d) in col_comments if c in core_set]
            if core_comments:
                if not tbl_comment:
                    out.write("\n-- Table comments\n")
                for (col, desc) in core_comments:
                    out.write(f"COMMENT ON COLUMN {fmt_fullname(table)}.{qident(col)} IS '{esc_literal(desc)}';\n")

            out.write("\n")
            return True

        # For other tables (e.g., lut_rli) continue to introspect from live DB
        columns = fetch_table_columns(cur, table)
        cons = fetch_constraints(cur, table)
        idxs = fetch_indexes(cur, table)
        tbl_comment = fetch_table_comment(cur, table)
        col_comments = fetch_column_comments(cur, table)

        # If table does not exist, skip
        if not columns:
            return False

        # Prepare sets of PK/UNIQUE constraint names to filter their implicit indexes
        pk_uk_names = {name for (name, contype, _def) in cons if contype in ("p", "u")}

        # Write header and DROP
        out.write("-- =============================================================================\n")
        if table == "lut_rli":
            out.write("-- TABLE: lut_rli (lookup table - Red List Index categories)\n")
            out.write("-- Reference table for extinction risk status categories\n")
        else:
            out.write(f"-- TABLE: {table}\n")
        out.write("-- =============================================================================\n")
        out.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")

        # CREATE TABLE
        out.write(build_create_table(table, columns))

        # Constraints as ALTER TABLE ... ADD CONSTRAINT
        for (name, _contype, condef) in cons:
            out.write(f"ALTER TABLE ONLY {fmt_fullname(table)} ADD CONSTRAINT {name} {condef};\n")

        # Indexes (filter out those that back PK/UNIQUE constraints)
        real_indexes = [(iname, idef) for (iname, idef) in idxs if iname not in pk_uk_names]
        if real_indexes:
            out.write("\n-- Indexes for %s\n" % table)
            for (_iname, idef) in real_indexes:
                out.write(idef.rstrip("\n") + "\n")

        # Comments
        if tbl_comment:
            out.write("\n-- Table comments\n")
            out.write(f"COMMENT ON TABLE {fmt_fullname(table)} IS '{esc_literal(tbl_comment)}';\n")
        if col_comments:
            if not tbl_comment:
                out.write("\n-- Table comments\n")
            for (col, desc) in col_comments:
                out.write(f"COMMENT ON COLUMN {fmt_fullname(table)}.{qident(col)} IS '{esc_literal(desc)}';\n")

        out.write("\n")
        return True

    # Helper: fetch function/procedure definitions by names
    def fetch_routines(cur, names: list):
        if not names:
            return []
        sql = """
            SELECT p.oid, p.proname, p.prokind
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = ANY(%s)
            ORDER BY p.proname
        """
        cur.execute(sql, (names,))
        rows = cur.fetchall() or []  # list of (oid, proname, prokind)
        defs = []
        for (oid, proname, prokind) in rows:
            cur.execute("SELECT pg_get_functiondef(%s)", (oid,))
            txt = cur.fetchone()[0]
            defs.append((proname, prokind, txt))
        return defs

    # Helper: fetch trigger definitions by names (non-internal only)
    def fetch_triggers(cur, names: list):
        if not names:
            return []
        sql = """
            SELECT t.oid, t.tgname, c.relname
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE NOT t.tgisinternal AND n.nspname = 'public' AND t.tgname = ANY(%s)
            ORDER BY t.tgname
        """
        cur.execute(sql, (names,))
        rows = cur.fetchall() or []  # list of (oid, tgname, relname)
        defs = []
        for (oid, tgname, relname) in rows:
            cur.execute("SELECT pg_get_triggerdef(%s)", (oid,))
            txt = cur.fetchone()[0]
            defs.append((tgname, relname, txt))
        return defs

    # Generate DDL strictly from live DB (no file fallback) and include routines/triggers
    with get_db_connection() as conn:
        cur = conn.cursor()
        with open(dest_path, "w", encoding="utf-8") as out:
            out.write("-- DDL output\n")
            # wlist section
            wrote_wlist = write_table_section(out, "wlist", cur)
            # lut_rli section
            wrote_lut = write_table_section(out, "lut_rli", cur)

            # If neither table was found, raise an error
            if not (wrote_wlist or wrote_lut):
                raise RuntimeError("No tables found in live DB for DDL export")

            # Routines and triggers required by issue
            required_routines = [
                'update_is_core',
                'update_ssp_required',
                'update_rli_required',
                'wlist_add_row',
                'wlist_delete_row',
            ]
            required_triggers = [
                'trg_update_is_core',
                'trg_update_ssp_required',
                'trg_update_rli_required',
            ]

            routine_defs = fetch_routines(cur, required_routines)
            trigger_defs = fetch_triggers(cur, required_triggers)

            # Verify presence; if any required are missing, raise with guidance for user to paste them
            present_routine_names = {name for (name, _k, _txt) in routine_defs}
            missing_routines = [n for n in required_routines if n not in present_routine_names]
            present_trigger_names = {name for (name, _rel, _txt) in trigger_defs}
            missing_triggers = [n for n in required_triggers if n not in present_trigger_names]

            if missing_routines or missing_triggers:
                missing_list = []
                if missing_routines:
                    missing_list.append(f"functions/procedures: {', '.join(missing_routines)}")
                if missing_triggers:
                    missing_list.append(f"triggers: {', '.join(missing_triggers)}")
                missing_txt = "; ".join(missing_list)
                raise RuntimeError(
                    "The following routines/triggers are not present in the database and thus cannot be exported to wlist.ddl: "
                    + missing_txt + ". Please paste their SQL definitions so we can include them."
                )

            if routine_defs:
                out.write("-- =============================================================================\n")
                out.write("-- ROUTINES (functions/procedures)\n")
                out.write("-- =============================================================================\n")
                for (_name, _k, fdef) in routine_defs:
                    # Ensure separation and end with newline
                    fdef_txt = fdef.rstrip() + "\n\n"
                    out.write(fdef_txt)

            if trigger_defs:
                out.write("-- =============================================================================\n")
                out.write("-- TRIGGERS\n")
                out.write("-- =============================================================================\n")
                for (tname, relname, tdef) in trigger_defs:
                    # Add DROP TRIGGER safety then CREATE from pg_get_triggerdef
                    out.write(f"DROP TRIGGER IF EXISTS {tname} ON public.{relname} CASCADE;\n")
                    out.write(tdef.rstrip() + "\n\n")

            # No relationships block appended; output is sourced only from the database.

#%%
# Generate the DQA (Data Quality Assessment) Markdown report to OUTPUT_DIR

def export_dqa_report(dest_path: str) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Map existing DCORE_* environment variables to connection args expected by wlist_dqa
    host = os.getenv("DCORE_HOST", "localhost")
    port = os.getenv("DCORE_PORT", "5432")
    dbname = os.getenv("DCORE_DB", "dcoredb")
    user = os.getenv("DCORE_USER", "glennehmke")
    # No hardcoded fallback (ecosystem D1 / wlist ADR-002): falls back to .pgpass if unset.
    password = os.getenv("DCORE_PASSWORD")

    args = SimpleNamespace(host=host, port=port, dbname=dbname, user=user, password=password, output=dest_path)

    # Use wlist_dqa helpers to build report
    conn = wlist_dqa.get_connection(args)
    try:
        cur = conn.cursor()
        db_info = f"{args.dbname} @ {args.host}:{args.port}"

        total, completeness_rows = wlist_dqa.assess_completeness(cur)
        ref_int = wlist_dqa.assess_referential_integrity(cur)
        constraints = wlist_dqa.assess_constraints(cur)
        duplicates = wlist_dqa.assess_duplicates(cur)
        coverage = wlist_dqa.assess_coverage(cur)

        # Include DB constraints and indexes so the report matches the dqa.md format
        try:
            db_constraints = wlist_dqa.fetch_db_constraints(cur)
        except Exception:
            db_constraints = []
        try:
            db_indexes = wlist_dqa.fetch_db_indexes(cur)
        except Exception:
            db_indexes = []

        try:
            db_routines = wlist_dqa.fetch_db_routines(cur)
        except Exception:
            db_routines = []
        try:
            db_triggers = wlist_dqa.fetch_db_triggers(cur)
        except Exception:
            db_triggers = []

        report = wlist_dqa.render_report(
            total, completeness_rows, ref_int, constraints, duplicates, coverage, db_info,
            db_constraints=db_constraints, db_indexes=db_indexes,
            db_routines=db_routines, db_triggers=db_triggers
        )

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(report)
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

#%%
def main() -> int:
    try:
        print("Fetching core wlist...", file=sys.stderr)
        df_core = fetch_dataframe(CORE_QUERY)
        print(f"  rows: {len(df_core)}", file=sys.stderr)

        print("Fetching lut_rli...", file=sys.stderr)
        df_rli = fetch_dataframe(RLI_QUERY)
        print(f"  rows: {len(df_rli)}", file=sys.stderr)

        print("Fetching avilist_changes...", file=sys.stderr)
        df_avilist_changes = fetch_dataframe(AVILIST_CHANGES_QUERY)
        print(f"  rows: {len(df_avilist_changes)}", file=sys.stderr)

        print(f"Writing CSVs to {OUTPUT_DIR}...", file=sys.stderr)
        export_csv(df_core, CORE_CSV)
        export_csv(df_rli, RLI_CSV)
        export_csv(df_avilist_changes, AVILIST_CHANGES_CSV)

        print(f"Writing SQL dump to {SQL_DUMP}...", file=sys.stderr)
        export_sql_dump({
            "public.wlist": df_core,
            "lut_rli": df_rli,
            "avilist_changes": df_avilist_changes,
        }, SQL_DUMP)

        print(f"Copying schema DDL to {DDL_EXPORT}...", file=sys.stderr)
        export_schema_ddl(DDL_EXPORT)

        print(f"Writing DQA report to {DQA_REPORT}...", file=sys.stderr)
        export_dqa_report(DQA_REPORT)

        print("Done.", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

#%%
if __name__ == "__main__":
    raise SystemExit(main())
