# wlist — Deep-dive Inventory

The grounded inventory of the `wlist` package: what exists, what's live vs dev vs dead, what each workflow does, and how it connects to the wider estate. Companion to [`00_strategy.md`](00_strategy.md) (the plan) and [`02_wlist_dev_log.md`](02_wlist_dev_log.md) (the decisions).

**Status:** Phase-1 inventory run 2026-07-05 (Cowork), immediately after promotion to top-level + `git init` (`D-023`). Nothing has been re-triaged yet — this is the **as-moved** tree (46 files, straight from `wdb/wlist` + nested `taxonomy/`). Findings that need Glenn's decision are called out; nothing risky has been changed on the strength of this pass alone.

---

## 1. Package layout (as-moved scan)

Currency per D-020/D-021: **LIVE** = canonical/deployed source of truth · **DEV** = work-in-progress/exemplar, not deployed · **DEAD** = candidate for `_archive/`.

| Path | Role | Currency | Notes |
|---|---|---|---|
| `README.md` | operational how-to for ingest/validate/archive-update | LIVE (docs) | ✅ Password default redacted 2026-07-05 (ADR-002). |
| `package_wlist.py` | `get_db_connection()`, CSV/SQL export (`wlist_core`, `lut_rli`, `avilist_changes`), `fetch_dataframe` | LIVE | ✅ `DCORE_PASSWORD` fallback redacted 2026-07-05 (ADR-002) — now `os.getenv("DCORE_PASSWORD")`, falls back to `~/.pgpass`. `OUTPUT_DIR` still hardcoded to `/Users/glennehmke/MEGA/Taxonomy/wlist` — the **other** "wlist" (Cowork data workspace), not this repo (§3 finding 3, still open). |
| `ingest_edited_wlist.py` | CLI: Excel → staging table → optional archive-and-replace of `public.wlist` | LIVE | Column-alignment + validation logic; per README. Not yet checked line-by-line this pass. |
| `validate_wlist_update.py` | standalone schema/row-count validator, gate before replace | LIVE | Exit code 4 on failure — used as a CI-style gate per README. |
| `backup.py` (+ `backup.log`, gitignored) | separate backup routine | LIVE (unverified) | Overlap with `ingest_edited_wlist.py --archive-and-update`'s own backup-schema step not yet reconciled — two backup mechanisms may exist side by side (open thread). |
| `wlist_dqa.py` + `wlist_dqa_report.md` | data-quality-assessment reporting | LIVE | ✅ Password default redacted 2026-07-05 (ADR-002). Report content not reviewed this pass. |
| `export_avilist_change_table.py`, `export_wlist_extended.py`, `find_unmatched_taxon_ids.py` | export/diagnostic utilities | LIVE (unverified) | Not yet read line-by-line; grouped here pending review. |
| `add_taxon/` | self-contained "add a new taxon" workflow | LIVE | `add_taxon.py`, `README.md`, `sample_add_taxon.csv`/`.json`, `wlist_add_taxon_guide.pdf`. ✅ `README.md` password default redacted 2026-07-05 (ADR-002). |
| `reconciliation/` | AviList change-class reporting | LIVE | `report_change_class.py`, `wlist_change_class_report.md`, `wlist_change_class_grouped_bar.png`, `integrated_changes.csv`. |
| `package/` | figshare packaging | LIVE | `figshare_create_draft.py` (wrapper) + `FIGSHARE_SUBMIT_README.md` + ✅ `figshare_submit.py` (copied in 2026-07-05, ADR-003 — was missing, now canonical here; sync to `Taxonomy/wlist/package/` before running). |
| `taxonomy/avilist_wlist_2025/` | 2025 AviList import/reconciliation (newly nested, ex-`wdb/taxonomy`) | LIVE/DEV mix | `import_avilist.py`, `check_csv_structure.py`, `check_wlist_structure.py`, `avilist_import_documentation.md`, plus a notebook + its `.html`/`.md` export (`wlist_avilist changes 2025.*`) — the notebook trio looks like a one-off analysis run rather than a repeatable script; candidate for a `demos/`-style home (range precedent) once confirmed. |
| `sql/` — core objects | `wlist_package.sql`, `w_add_row.sql`, `w_delete_row.sql`, `w_is_core.sql`, `w_check_ssp_required.sql` | LIVE | Not yet verified against the deployed `dcoredb` procedures (§4). |
| `sql/` — import/reconciliation scripts | `avilist_import.sql`, `AviList_wlist_integration.sql`, `WLAB.sql`, `WLAB_add taxon and shuffle sort.sql`, `add or match abd fields to wlist.sql`, `archive_and_update wlist.sql`, `import and match ala through galah.sql`, `version reconciliation.sql`, `ds_sensitive_reco.sql` | LIVE (ops-like) | Mixed runtime/diagnostic, not yet split by D-021 convention. |
| `sql/wlist_al_2025.sql.bak` | backup copy sitting in live `sql/` | DEAD (candidate) | Classic D-020/D-021 case — a `.bak` file in the live tree with no explicit tier. Not yet moved (this pass is inventory-only). |
| `wlist_package.md` | packaging output spec + field dictionary | LIVE (docs) | ✅ Password default redacted 2026-07-05 (ADR-002). Useful field-level metadata for `public.wlist`/`lut_rli`/`avilist_changes` — worth keeping current. |
| `.DS_Store`, `__pycache__/` | OS/Python scratch | scratch | Now covered by the new `.gitignore` (this pass). |

**Not moved with the package (left in `applied_projects`, per D-023's result note):** `wlist_backup/` (dated subfolder `20260412_133657`) — a wlist-specific backup snapshot. Needs reconciling against `backup.py`'s own behaviour before deciding whether it belongs inside `wlist/_archive/` or stays a separate backup-tier concern.

## 2. Live workflows — what each does

**A. Ingest → validate → archive-and-update (the core update cycle):** an edited wlist Excel is loaded into a staging table matching the live schema (`ingest_edited_wlist.py`), optionally validated standalone (`validate_wlist_update.py`), then `archive_and_update` backs up `public.wlist` (preferring a `backup` schema, falling back to `public.wlist_YYYYMMDD`), truncates and reloads it, verifies the row count, and drops the staging table. This is the mechanism that keeps the taxonomic backbone current as AviList/BirdLife updates land.

**B. Add-taxon:** `add_taxon/add_taxon.py` — a narrower, sample-driven path (CSV/JSON templates + a PDF guide) for adding a single new taxon without going through the full ingest cycle.

**C. DQA reporting:** `wlist_dqa.py` produces `wlist_dqa_report.md` — a data-quality pass over the live table (not yet reviewed for what checks it runs).

**D. Reconciliation:** `reconciliation/report_change_class.py` classifies AviList changes (Implementable / Not implementable / Partially implementable — see `wlist_package.md`'s changelog table) and produces a report + chart; `taxonomy/avilist_wlist_2025/` is the underlying 2025 AviList import/comparison work this draws on.

**E. Packaging + figshare:** `package_wlist.py` exports `wlist_core.csv`, `lut_rli.csv`, `avilist_changes.csv`, `wlist_core.sql`, and a DDL copy to the **Taxonomy/wlist data workspace** (`OUTPUT_DIR`, hardcoded); `package/figshare_create_draft.py` is meant to then push that package to a private Figshare draft — currently non-functional from this repo alone (§3).

## 3. Cross-location & security findings (see `02_wlist_dev_log.md` for full ADRs)

1. **✅ Hardcoded DB credentials (mirrored ecosystem `D1`) — redacted 2026-07-05.** `package_wlist.py`, `wlist_dqa.py` no longer fall back to a literal default password; `README.md`, `add_taxon/README.md`, and `wlist_package.md` no longer document one. **ADR-002** (accepted, option 2). **Still open:** the old literal value remains in this repo's git history (root commit) — the sandbox couldn't rewrite history (see the environment note in project memory), so Glenn needs to do a one-time `rm -rf .git && git init` from his own terminal to fully clear it (instructions in ADR-002).
2. **✅ Broken `figshare_submit.py` reference — fixed 2026-07-05.** `figshare_submit.py` copied into `package/` here (was previously only at `MEGA/Taxonomy/wlist/package/figshare_submit.py`, the Cowork data workspace). **ADR-003** (accepted, option 1). This repo's copy is now the one to edit; sync to the data workspace before actually running a submission (see `FIGSHARE_SUBMIT_README.md`).
3. **The two "wlist"s are linked by an undocumented output contract.** `package_wlist.py`'s `OUTPUT_DIR` writes packaging outputs straight into `MEGA/Taxonomy/wlist` — i.e., the code repo's packaging step targets the *other* wlist's folder. Worth documenting explicitly (as a mini data contract, same spirit as ecosystem `D14`) so a future move of either location doesn't silently break packaging. **Still open.**

## 4. DB objects (verify against `dcoredb`)

Per the ecosystem map (§3), `wlist` produces `public.wlist` (+ `wlist_covariates`, `wlist_range`, views) via `update_is_core()` and reconciliation queries. This pass has **not** verified the repo's `sql/*.sql` procedure bodies against what's actually deployed in `dcoredb` — flagged for the Claude Code side of this review (per `WORKING_PRACTICES.md`, DB verification is Claude Code's job; Cowork can't reach the live DB). Candidates to check first: `w_is_core.sql` (backs `update_is_core()`?), `w_add_row.sql`/`w_delete_row.sql`, and whether `sql/wlist_al_2025.sql.bak` differs meaningfully from the live `wlist_al_2025.sql`.

## 5. Consumers & data contracts

- **`range`, `sites`, `trends` all join to `public.wlist`** for species identity — the single most cross-cutting dependency in the ecosystem (more so than `range_in_region`, which is a `D14`-documented two-package contract; this is a four-package one that isn't yet documented as such).
- Ecosystem `D12` ("many parallel `wlist_*` tables coexist in `public`") is the standing open question about which table is canonical — unresolved, and squarely in this package's remit now that it has its own strategy home.

## 6. Open threads
See [`02_wlist_dev_log.md`](02_wlist_dev_log.md): credential redaction + rotation call (ADR-002); `figshare_submit.py` location (ADR-003); `.bak` quarantine + `wlist_backup/` reconciliation; `backup.py` vs. `archive_and_update`'s built-in backup (possible duplication); `D12` canonical-table design; DB-object verification (Claude Code).
