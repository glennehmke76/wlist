#%%
"""
Generate a Markdown report summarising change_class and change_class_avilist from wlist,
using value descriptions from dcoredb.wlist_change_class, grouped by taxon_level.

- Connects via wlist.package_wlist.get_db_connection()
- Joins wlist to wlist_change_class twice to resolve both fields to descriptions
- Summarises frequency of values by taxon_level for both fields
- Highlights rows where both fields have values
- Writes Markdown to /Users/glennehmke/MEGA/py_proj/wabd/wlist/reconciliation/wlist_change_class_report.md

Run:
  python -m wlist.reconciliation.report_change_class

Requires:
  pip install pandas psycopg2-binary

DB connection env vars (delegated to package_wlist):
  DCORE_HOST, DCORE_DB, DCORE_USER, DCORE_PASSWORD, DCORE_PORT
"""
#%%
from __future__ import annotations
import os
import sys
from typing import List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Ensure project root on sys.path when run directly from repository
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(HERE)
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# Import DB/output helpers
try:
    from wlist import package_wlist as pw  # type: ignore
except Exception:  # pragma: no cover
    import package_wlist as pw  # type: ignore

OUTPUT_MD = os.path.join("/Users/glennehmke/MEGA/py_proj/wabd/wlist/reconciliation", "wlist_change_class_report.md")
INTEGRATED_CSV = os.path.join("/Users/glennehmke/MEGA/py_proj/wabd/wlist/reconciliation", "integrated_changes.csv")

SQL = (
    """
    SELECT
      w.taxon_level,
      w.taxon_id,
      w.taxon_name,
      w.change_class,
      w.change_class_avilist,
      c1.id AS change_class_id,
      c1.description AS change_class_desc,
      c2.id AS change_class_avilist_id,
      c2.description AS change_class_avilist_desc
    FROM wlist w
    LEFT JOIN wlist_change_class c1 ON w.change_class = c1.id
    LEFT JOIN wlist_change_class c2 ON w.change_class_avilist = c2.id
    ORDER BY w.taxon_sort
    ;
    """
)

SQL_CLASSES = (
    """
    SELECT id, description
    FROM wlist_change_class
    ORDER BY id
    ;
    """
)


def fetch_df() -> pd.DataFrame:
    with pw.get_db_connection() as conn:
        df = pd.read_sql(SQL, conn)
    return df


def fetch_classes_df() -> pd.DataFrame:
    with pw.get_db_connection() as conn:
        classes = pd.read_sql(SQL_CLASSES, conn)
    return classes


SQL_TOTALS = (
    """
    SELECT
      COUNT(*) AS total_rows,
      COUNT(w.change_class) AS change_class_non_null,
      COUNT(w.change_class_avilist) AS change_class_avilist_non_null,
      COUNT(*) FILTER (WHERE w.change_class IS NOT NULL OR w.change_class_avilist IS NOT NULL) AS num_changes
    FROM wlist w
    ;
    """
)

def fetch_overall_totals() -> pd.DataFrame:
    with pw.get_db_connection() as conn:
        return pd.read_sql(SQL_TOTALS, conn)


def fetch_changes_by_class_tranche() -> pd.DataFrame:
    # Summary by taxon_level (tranche) and class, for both fields side-by-side
    sql = (
        """
        WITH cc AS (
          SELECT w.taxon_level, c.id AS class_id, c.description, COUNT(*) AS cc_count
          FROM wlist w
          JOIN wlist_change_class c ON w.change_class = c.id
          GROUP BY w.taxon_level, c.id, c.description
        ),
        cca AS (
          SELECT w.taxon_level, c.id AS class_id, c.description, COUNT(*) AS cca_count
          FROM wlist w
          JOIN wlist_change_class c ON w.change_class_avilist = c.id
          GROUP BY w.taxon_level, c.id, c.description
        )
        SELECT COALESCE(cc.taxon_level, cca.taxon_level) AS taxon_level,
               COALESCE(cc.class_id, cca.class_id) AS class_id,
               COALESCE(cc.description, cca.description) AS description,
               COALESCE(cc.cc_count, 0) AS change_class_freq,
               COALESCE(cca.cca_count, 0) AS change_class_avilist_freq
        FROM cc
        FULL OUTER JOIN cca
          ON cc.taxon_level = cca.taxon_level AND cc.class_id = cca.class_id
        ORDER BY taxon_level, class_id
        ;
        """
    )
    with pw.get_db_connection() as conn:
        return pd.read_sql(sql, conn)


def _freq_by_level(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    # Treat missing as explicit label for reporting
    work = df.copy()
    work[value_col] = work[value_col].fillna("Missing")
    g = work.groupby(["taxon_level", value_col], dropna=False).size().reset_index(name="count")
    # Sort: by taxon_level, then descending count, then value
    g = g.sort_values(["taxon_level", "count", value_col], ascending=[True, False, True])
    return g


def _to_md_table(df: pd.DataFrame, headers: List[str]) -> str:
    # Simple GitHub-flavoured Markdown table
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        vals = [str(row[h]) if pd.notna(row[h]) else "" for h in headers]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def build_report(
    df: pd.DataFrame,
    totals_sql: pd.DataFrame,
    classes_df: pd.DataFrame,
    figures_dir: str,
) -> str:
    total_rows = int(totals_sql.loc[0, "total_rows"]) if not totals_sql.empty else len(df)
    cc_non_null = int(totals_sql.loc[0, "change_class_non_null"]) if not totals_sql.empty else int(df["change_class"].notna().sum())
    cca_non_null = int(totals_sql.loc[0, "change_class_avilist_non_null"]) if not totals_sql.empty else int(df["change_class_avilist"].notna().sum())
    num_changes = int(totals_sql.loc[0, "num_changes"]) if not totals_sql.empty else int(((df["change_class"].notna()) | (df["change_class_avilist"].notna())).sum())

    # Frequency summaries (existing)
    freq_cc = _freq_by_level(df, "change_class_desc")
    freq_cca = _freq_by_level(df, "change_class_avilist_desc")

    # Overall counts by ID and description (exclude NULLs)
    overall_cc = (
        df.dropna(subset=["change_class_id"]).copy()
          .groupby(["change_class_id", "change_class_desc"]).size().reset_index(name="count")
          .sort_values(["change_class_id"]).reset_index(drop=True)
    )
    overall_cca = (
        df.dropna(subset=["change_class_avilist_id"]).copy()
          .groupby(["change_class_avilist_id", "change_class_avilist_desc"]).size().reset_index(name="count")
          .sort_values(["change_class_avilist_id"]).reset_index(drop=True)
    )

    # Rows with both fields populated (retain)
    both = df[df["change_class_desc"].notna() & df["change_class_avilist_desc"].notna()].copy()
    both_counts = (
        both.groupby("taxon_level").size().reset_index(name="rows_with_both")
            .sort_values(["rows_with_both", "taxon_level"], ascending=[False, True])
    )

    # Prepare overall by class (for bar chart), ordered by class id
    cc_counts = df["change_class_id"].value_counts().rename_axis("id").reset_index(name="change_class_freq")
    cca_counts = df["change_class_avilist_id"].value_counts().rename_axis("id").reset_index(name="change_class_avilist_freq")
    by_class = classes_df.copy()
    by_class = by_class.merge(cc_counts, how="left", on="id").merge(cca_counts, how="left", on="id")
    by_class[["change_class_freq", "change_class_avilist_freq"]] = by_class[["change_class_freq", "change_class_avilist_freq"]].fillna(0).astype(int)

    # Build Markdown
    parts: List[str] = []
    a = parts.append

    a(f"# A working list (wlist) integrated reconciliation of v2-v4 and AviList changes\n")
    a("")
    a(f"- Total rows in wlist: {total_rows}")
    a(f"- change_class populated: {cc_non_null}")
    a(f"- change_class_avilist populated: {cca_non_null}")
    a(f"- Total # changes: {num_changes}")
    a("")
    a("_Table generation code_")
    a("```sql")
    a(SQL_TOTALS.strip())
    a("```")
    a("")
    # Note about export file placed before the '# changes by type' section
    a(f"Note: Exported integrated table to {os.path.basename(INTEGRATED_CSV)}")
    a("")

    # Grouped bar chart
    fig_path = os.path.join(figures_dir, "wlist_change_class_grouped_bar.png")
    try:
        labels = by_class["id"].astype(str).tolist()
        x = np.arange(len(labels))
        width = 0.38
        fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.6), 5.5), dpi=160)
        rects1 = ax.bar(x - width/2, by_class["change_class_freq"].values, width,
                        label="change_class", color="#4C72B0", edgecolor="#2B3E63")
        rects2 = ax.bar(x + width/2, by_class["change_class_avilist_freq"].values, width,
                        label="change_class_avilist", color="#55A868", edgecolor="#2E6D4C")
        ax.set_ylabel("# changes")
        ax.set_title("# changes by type (class)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend(frameon=False, ncols=2, loc="upper right")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        os.makedirs(os.path.dirname(fig_path), exist_ok=True)
        fig.savefig(fig_path)
        plt.close(fig)
        a("## # changes by type")
        a(f"![Grouped bar chart]({fig_path})")
        a("")
    except Exception as e:  # pragma: no cover
        a(f"[Chart generation failed: {e}]")
        a("")

    a("## Overall frequency – change_class")
    a(_to_md_table(overall_cc, ["change_class_id", "change_class_desc", "count"]))
    a("")
    a("_Table generation code_")
    a("```sql")
    a(SQL.strip())
    a("```")
    a("")

    a("## Overall frequency – change_class_avilist")
    a(_to_md_table(overall_cca, ["change_class_avilist_id", "change_class_avilist_desc", "count"]))
    a("")
    a("_Table generation code_")
    a("```sql")
    a(SQL.strip())
    a("```")
    a("")

    a("## Highlight: rows with values in BOTH fields")
    if both.empty:
        a("No rows have both change_class and change_class_avilist populated.")
    else:
        a(f"Total rows with both fields populated: {len(both)}")
        a("")
        detail_cols = [
            "taxon_level", "taxon_id", "taxon_name",
            "change_class_desc", "change_class_avilist_desc",
        ]
        a("Detailed rows (both values present):")
        a(_to_md_table(both[detail_cols], detail_cols))
        a("")
        a("_Table generation code_")
        a("```sql")
        a(SQL.strip())
        a("```")
    a("")

    return "\n".join(parts)


def write_report(md: str, dest_path: str) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Report written to: {dest_path}")


def main() -> None:
    df = fetch_df()
    # Export integrated table of changes
    os.makedirs(os.path.dirname(INTEGRATED_CSV), exist_ok=True)
    df.to_csv(INTEGRATED_CSV, index=False)

    totals = fetch_overall_totals()
    classes = fetch_classes_df()
    figures_dir = os.path.dirname(OUTPUT_MD)
    md = build_report(df, totals, classes, figures_dir)
    write_report(md, OUTPUT_MD)


if __name__ == "__main__":
    main()
