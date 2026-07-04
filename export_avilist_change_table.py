#%%
"""
Export a formatted multi-page PDF table of Avilist change statuses from the wlist table.

- Connects via wlist.package_wlist.get_db_connection()
- Executes the provided SQL (see SQL constant below)
- Outputs to: /Users/glennehmke/MEGA/Taxonomy/wlist/wlist_avilist_changes.pdf
- Formatting: header band, zebra rows, grid lines; "Avilist change note" column wrapped.

Requirements:
  pip install reportlab pandas psycopg2-binary

DB connection env vars (delegated to package_wlist):
  DCORE_HOST, DCORE_DB, DCORE_USER, DCORE_PASSWORD, DCORE_PORT

Run:
  python -m wlist.export_avilist_change_table
"""
#%%
from __future__ import annotations
import os
import sys
from typing import List

import pandas as pd

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Ensure project root on sys.path when run directly from repository
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(HERE)
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# Import DB helper (support both package and script execution contexts)
try:
    from . import package_wlist as pw  # type: ignore
except Exception:  # pragma: no cover
    import package_wlist as pw  # type: ignore

# Output
OUTPUT_DIR = "/Users/glennehmke/MEGA/Taxonomy/wlist/package"
PDF_PATH = os.path.join(OUTPUT_DIR, "wlist_avilist_changes.pdf")

# SQL from issue description
SQL = (
    """
SELECT
  wlist.taxon_name AS "Taxon name",
  wlist. taxon_scientific_name as "Taxon scientific name",
  CASE
    WHEN wlist.alist_change = 1 THEN ''
    WHEN wlist.alist_change = 0 THEN 'Not implementable'
    WHEN wlist.alist_change = 0.5 THEN 'Partially implementable'
    ELSE NULL END AS "Avilist change status",
  wlist.alist_change_note AS "Avilist change note"
FROM wlist
WHERE
  wlist.alist_change IS NOT NULL
ORDER BY wlist.taxon_sort
;
"""
)


def fetch_df() -> pd.DataFrame:
    with pw.get_db_connection() as conn:
        df = pd.read_sql(SQL, conn)
    # Ensure column order as in SQL labels
    expected_cols = [
        "Taxon name",
        "Taxon scientific name",
        "Avilist change status",
        "Avilist change note",
    ]
    # Keep only expected columns in order (ignore extras just in case)
    df = df[[c for c in expected_cols if c in df.columns]]
    return df


def build_pdf(df: pd.DataFrame, dest_path: str) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Page and margins
    pagesize = A4
    left_margin = right_margin = 0.5 * inch
    top_margin = 0.5 * inch
    bottom_margin = 0.6 * inch

    doc = SimpleDocTemplate(
        dest_path,
        pagesize=pagesize,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title="WLIST Avilist Change Table",
        author="wlist tools",
    )

    # Styles
    styles = getSampleStyleSheet()
    body_style: ParagraphStyle = styles["BodyText"].clone("CellBody")
    body_style.fontName = "Helvetica"
    body_style.fontSize = 8
    body_style.leading = 10
    body_style.spaceBefore = 0
    body_style.spaceAfter = 0
    body_style.allowOrphans = 0
    body_style.allowWidows = 0

    note_style: ParagraphStyle = body_style.clone("NoteBody")
    note_style.wordWrap = "CJK"  # more tolerant wrapper for long tokens

    header_style: ParagraphStyle = styles["Heading4"].clone("HeaderCell")
    header_style.fontName = "Helvetica-Bold"
    header_style.fontSize = 9
    header_style.leading = 11
    header_style.spaceBefore = 0
    header_style.spaceAfter = 0

    # Compute column widths proportionally for landscape A4
    avail_width = pagesize[0] - left_margin - right_margin
    # width shares for columns: name, sci name, status, note
    shares = [0.20, 0.28, 0.16, 0.36]
    col_widths = [avail_width * s for s in shares]

    # Build table data
    headers = list(df.columns)
    header_paras = [Paragraph(str(h), header_style) for h in headers]

    data: List[List[object]] = [header_paras]
    for _, row in df.iterrows():
        name = Paragraph("" if pd.isna(row[0]) else str(row[0]), body_style)
        sci = Paragraph("" if pd.isna(row[1]) else str(row[1]), body_style)
        status = Paragraph("" if pd.isna(row[2]) else str(row[2]), body_style)
        note_text = "" if pd.isna(row[3]) else str(row[3])
        note = Paragraph(note_text, note_style)
        data.append([name, sci, status, note])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)

    # Table styling
    ts = TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eef8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c0c7cf")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.Color(1, 1, 1)]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ])
    tbl.setStyle(ts)

    story = [tbl]

    doc.build(story)


def main() -> None:
    df = fetch_df()
    build_pdf(df, PDF_PATH)
    print(f"Wrote PDF: {PDF_PATH}  (rows: {len(df)})")


if __name__ == "__main__":
    main()
