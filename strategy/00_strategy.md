# wlist — Strategy & Master Plan

Entry point for the `wlist` architecture review. Applies the method in [`../../WORKFLOW_RATIONALIZATION_PLAYBOOK.md`](../../WORKFLOW_RATIONALIZATION_PLAYBOOK.md). Scaffolded 2026-07-05 (Cowork) from the `range`/`sites`/`trends` project template, immediately following its promotion to a top-level package (ecosystem `D-023`).

**Project:** wlist (the Working [bird] List — Australia's authoritative working taxonomic checklist; the taxonomy domain package)
**Reviewer/architect:** Glenn
**Conceptual parent:** TheEvidenceBase (see ecosystem map §0); `wlist` is the **taxonomic backbone** everything else (`range`, `sites`, `trends`) joins to.
**Maturity:** working end-to-end tooling exists (ingest/validate/archive-update, DQA reporting, figshare packaging, an `add_taxon` workflow, an AviList 2025 reconciliation pass), but it was **never independently versioned** until this pass and carries at least one live security issue (see §3) and one broken cross-location dependency (§3).
**Status:** SEED — just promoted to a top-level package + git repo (`D-023`, executed 2026-07-05). This doc starts the Phase-1 inventory; deep triage continues in `01_wlist_deepdive.md`.

---

## 1. Goals (this engagement)

1. Understand how the `wlist` ingest → validate → archive/update → package/DQA → figshare-publish workflow fits together, and how `range`/`sites`/`trends` and the `taxonomy/avilist_wlist_2025` reconciliation work depend on it.
2. **Security first-pass:** a default DB password is hardcoded (as an `os.getenv` fallback) across multiple files and now sits in the fresh git history — this needs a decision before the repo goes anywhere near a remote (see D-001 precedent in the ecosystem log; `02_wlist_dev_log.md` ADR-002).
3. **Triage** the tree using the D-020/D-021 currency model (live / `_dev/` / `_archive/`) — flag backup/scratch files sitting in the live tree (e.g. `sql/wlist_al_2025.sql.bak`).
4. Map the **two "wlist" locations** explicitly as a documented contract: the code package (`py_proj/wlist`, this repo) and the Cowork data/docs workspace (`MEGA/Taxonomy/wlist`, where `package_wlist.py`'s hardcoded `OUTPUT_DIR` writes, and where the figshare packaging inputs currently live) — see the broken `figshare_submit.py` cross-location dependency in §3.
5. Produce a grounded inventory + first master-plan skeleton, recording decisions in the dev log.

**Explicitly out of scope this pass:** publishing anything to figshare; rotating the exposed DB password (Glenn's call — flagged, not executed); full package formalisation (`pyproject`/`resources/sql` layout matching `sites`/`trends`); resolving the `taxonomy/` reconciliation content itself.

## 2. Cross-project context — TheEvidenceBase + who consumes wlist

`wlist` is one of the four core `py_proj` domain packages (ecosystem map §3), alongside `range`, `sites`, `trends` — but the **only one that is a shared dependency of the other three**, not a peer consumer:

- **Taxonomy (`wlist`) is the join key for everything.** `range`, `sites`, and `trends` all resolve species identity against `public.wlist` (+ `wlist_covariates`, `wlist_range`, views). Ecosystem `D12` ("wlist version policy") already flags that many parallel `wlist_*` tables coexist in `public` — a single canonical table + changelog is still an open decision.
- **Figshare-published, citable.** Existing figshare draft workflow (not yet finalised — see project memory `figshare-wlist-submission.md`). This is why `wlist`'s own git/versioning matters independently of the other packages' timelines (ecosystem `D5`).
- **Two physically separate "wlist" locations, on purpose:** the code package (`py_proj/wlist`, versioned, this repo) and the Cowork data/docs workspace (`MEGA/Taxonomy/wlist` — spreadsheets, AviList working files, DQA outputs, `wlist.drawio`). `package_wlist.py`'s `OUTPUT_DIR` is hardcoded to the latter, so the two are linked by a real (if implicit) file-output contract — worth making explicit rather than just "known".

## 3. What we already know about `wlist` (first pass, 2026-07-05)

Live surfaces (kept, in place):
- **Ingest/validate/update trio** — `ingest_edited_wlist.py`, `validate_wlist_update.py`, `package_wlist.py` (also holds `get_db_connection`). Documented in `README.md`: ingest an edited Excel → staging table → validated archive-and-replace of `public.wlist`, with an automatic `backup` schema fallback to `public`.
- **`backup.py`** — a separate backup routine (`backup.log` alongside it — gitignored).
- **`wlist_dqa.py`** + `wlist_dqa_report.md` — data-quality-assessment reporting.
- **`add_taxon/`** — a self-contained mini-workflow (README, sample CSV/JSON, a PDF guide) for adding a new taxon.
- **`reconciliation/`** — AviList change-class reporting (`report_change_class.py`, a grouped-bar PNG, a markdown report, `integrated_changes.csv`).
- **`package/`** — figshare packaging: `figshare_create_draft.py` (CLI wrapper) + `FIGSHARE_SUBMIT_README.md`.
- **`taxonomy/avilist_wlist_2025/`** (newly nested, ex-`wdb/taxonomy`) — the 2025 AviList import/reconciliation notebook + supporting scripts (`check_csv_structure.py`, `check_wlist_structure.py`, `import_avilist.py`).
- **`sql/`** — ~14 files: core DDL/procedures (`wlist_package.sql`, `w_add_row.sql`, `w_delete_row.sql`, `w_is_core.sql`, `w_check_ssp_required.sql`) plus import/reconciliation scripts (`avilist_import.sql`, `AviList_wlist_integration.sql`, `WLAB.sql`, `version reconciliation.sql`, `ds_sensitive_reco.sql`).

**Two findings that need a decision before this goes further (full detail + ADRs in `02_wlist_dev_log.md`):**

1. **✅ Hardcoded default DB password — redacted 2026-07-05.** `package_wlist.py`, `wlist_dqa.py`, and the three READMEs no longer carry the literal default. Mirrors the exact issue the ecosystem log already flagged for `sys_py/config.py` (`D1`). **Still open:** the old value remains in this repo's git history (root commit) — the sandbox couldn't rewrite history (file deletion is blocked on this mount), so Glenn needs a one-time `rm -rf .git && git init` from his own terminal to fully clear it (copy-paste steps in ADR-002; safe, no remote exists). Rotation of the actual `dcoredb` password itself was **not** requested — Glenn's call to leave for now. See ADR-002.
2. **✅ Broken cross-location script reference — fixed 2026-07-05.** `figshare_submit.py` is now copied into `package/` here (was previously only at `MEGA/Taxonomy/wlist/package/figshare_submit.py`, the data workspace). This repo's copy is now the one to edit; sync to the data workspace before actually running a submission (noted in `FIGSHARE_SUBMIT_README.md`). See ADR-003.

Also present, not yet triaged: `sql/wlist_al_2025.sql.bak` (a `.bak` file inside the live `sql/` tree — D-020/D-021 candidate for `_archive/` or `_dev/`); `wlist_backup/` was **not** moved with this package (left in `applied_projects`, flagged in `D-023`'s result note) — needs reconciling with `backup.py`'s own backup behaviour before deciding where it belongs.

See [`01_wlist_deepdive.md`](01_wlist_deepdive.md) for the full grounded inventory and triage dispositions.

## 4. Two-track plan

- **Track A — legibility + safety (this pass):** resolve the credential exposure (ADR-002); resolve or document the `figshare_submit.py` location (ADR-003); quarantine `.bak`/scratch files to `_archive/`/`_dev/`; decide `wlist_backup/`'s home.
- **Track B — formalisation (deferred):** `pyproject`/`resources/sql/{runtime,ops}` layout matching `sites`/`trends`; consolidate onto `sys_py`'s connector pattern (or the trends `db/` module template) rather than each script rolling its own `get_db_connection`; resolve the `D12` "many parallel `wlist_*` tables" versioning question; formal data contract doc for `range`/`sites`/`trends` consumption (extends `D14`).

## 5. Method & conventions (inherited — do not reinvent)

This project **inherits** the ecosystem conventions; it does not redefine them:
- **Decision logs (two-scope):** `wlist` decisions = `ADR-` in [`02_wlist_dev_log.md`](02_wlist_dev_log.md); cross-package/shared-substrate = `D-` in `../../strategy_ecosystem/01_ecosystem_dev_log.md` (project ADRs link *up* — this project's very existence at top-level links up to `D-023`).
- **Currency tiers (D-020/D-021):** live = canonical source; WIP = `_dev/`; dead = `_archive/` (agents never sweep `_archive/`). `wlist` **is now** under git (`master`, root-commit `cc70263`), so `_archive/` + git history together retain provenance going forward.
- **Working practices:** `../../WORKING_PRACTICES.md` (repo docs are the memory; git novice cheat sheet for any git steps).
- **Credentials:** no hardcoded secrets — env/`.env`/`~/.pgpass` only (ecosystem `D1`); `wlist` is currently **out of line** with this (see §3 finding 1).

## 6. Open threads
See [`02_wlist_dev_log.md`](02_wlist_dev_log.md) open threads: credential redaction + rotation call (ADR-002); `figshare_submit.py` location decision (ADR-003); `.bak`/scratch quarantine; `wlist_backup/` reconciliation; `D12` canonical-table/changelog design; package formalisation.

---
*Scaffolded from `range`/`sites`/`trends` `strategy/` per the playbook's "new-package scaffold" (§5a).*
