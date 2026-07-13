# Hand-off — wlist re-architecture 2.0, Track B (DB + terminal steps)

**From:** Cowork session, 2026-07-13 (re-architecture 2.0).
**To:** Claude Code (has live `dcoredb` access) + Glenn's terminal (deletes/cross-mount).
**Why a hand-off:** these steps need capabilities Cowork lacks — live DB verification,
file deletion (the Cowork FUSE mount blocks `unlink`/`rmdir`), and cross-mount moves
(`Taxonomy/wlist` ↔ `py_proj/wlist`). The **plan, decisions, and safe skeleton are
already done** — see `03_wlist_architecture_target.md` and dev-log ADR-004/005/006
(ecosystem D-061). This brief is only the execution of the deferred parts.

**Ground rules (inherit, don't reinvent):** CLAUDE.md conventions apply —
`resources/sql/{runtime,ops}` = deployed source of truth; never touch `_archive/`;
promotion rule (a `_dev`/loose object confirmed deployed → move its source into
`resources/sql/`); no hardcoded credentials (use `~/.pgpass`); record each decision as
a dated ADR in `strategy/02_wlist_dev_log.md` in the same session. Work on a branch
(`git checkout -b wlist-trackB`); `master` stays the safe harbour.

---

## Step 1 — Classify `sql/*` into `resources/sql/{runtime,ops}` (DB verify)

The `resources/sql/{runtime,ops}/` folders + `resources/sql/README.md` skeleton already
exist. The 14 files in `sql/` still need classifying **against what is actually deployed
in `dcoredb`** — do not trust filenames alone.

For each `sql/*.sql`, determine whether the object it defines is **live in `dcoredb`**:
- Compare the file's function/procedure body to `pg_get_functiondef(...)` (or `\df+`,
  `\d+` for tables/views) for the matching object name.
- **Deployed + is the source of truth** → `git mv` into `resources/sql/runtime/`.
- **One-off / diagnostic / import / reconciliation, not a deployed live object** →
  `git mv` into `resources/sql/ops/`.
- **Dead / superseded** → `_archive/` (already done for `wlist_al_2025.sql.bak`).

Provisional split to verify (from `03_wlist_architecture_target.md` §6):
- *Likely runtime:* `w_add_row.sql`, `w_delete_row.sql`, `w_is_core.sql`,
  `w_check_ssp_required.sql`, `wlist_package.sql`, `wlist_ddl.sql`.
- *Likely ops:* `avilist_import.sql`, `AviList_wlist_integration.sql`, `WLAB.sql`,
  `WLAB_add taxon and shuffle sort.sql`, `add or match abd fields to wlist.sql`,
  `archive_and_update wlist.sql`, `import and match ala through galah.sql`,
  `version reconciliation.sql`, `ds_sensitive_reco.sql`, `wlist_al_2025.sql`.

**Watch for:** if any deployed `wlist` procedure joins `survey`↔`sighting`, apply
ecosystem **D-060** (composite key `(data_source, id)`). Also check the `wlist` canonical
table question (ecosystem **D12** — many parallel `wlist_*` tables) while you're in the DB;
that's this domain's open remit but out of scope for this hand-off unless trivially adjacent.
Record the classification outcome as an ADR (which files were live, any surprises).

## Step 2 — Refactor loose root scripts into the `wlist/` code package

Target (see `03_...` §3): a `wlist/wlist/` code package split by role.
- `wlist/core/` — extract `get_db_connection` (currently inside `package_wlist.py`);
  consolidate onto the `sys_py` connector where practical (ties to deferred **D-015** —
  note it, don't force it if it balloons scope).
- `wlist/ingest/` — `ingest_edited_wlist.py`, `validate_wlist_update.py`.
- `wlist/build/` — `package_wlist.py`, `export_avilist_change_table.py`, `wlist_dqa.py`
  (data-package builders).
- `wlist/tools/` — `export_wlist_extended.py`, `find_unmatched_taxon_ids.py`, `backup.py`
  (internal utilities, **not** part of the data package).
- Add `wlist/__init__.py` (+ sub-package `__init__.py`s), `pyproject.toml`, `MANIFEST.in`
  mirroring `trends`.

**Coupling to fix on move (verified this session):**
- `wlist_dqa.py` reads `wlist_ddl.sql` via `os.path.join(here, "wlist_ddl.sql")` — after
  the move that relative path breaks. Repoint it at the `resources/sql/runtime/` (or
  `ops/`) home of `wlist_ddl.sql`.
- Root scripts do **not** cross-import each other (each is a standalone CLI), so no
  internal import graph to untangle — but update any `python -m wlist.<script>` run
  commands in READMEs to the new module paths.

## Step 3 — Retarget `OUTPUT_DIR` and collapse the two-location split

`package_wlist.py` and `export_avilist_change_table.py` hardcode
`OUTPUT_DIR = "/Users/glennehmke/MEGA/Taxonomy/wlist/package"`. Retarget both to the
in-repo `data_package/build/` (ADR-005). Also repoint `package/figshare_submit.py`'s
`PACKAGE_DIR` at `data_package/build/`, collapsing the ADR-003 "edit here, run there"
split. Move the figshare tooling under `data_package/figshare/`. Do a dry build and
confirm outputs land inside the repo. Decide whether `data_package/build/` is
git-tracked or git-ignored (built artifacts — likely ignore, keep only the committed
inputs + `DATA_PACKAGE.md`).

## Step 4 — Consolidate existing built outputs (Glenn's terminal, cross-mount)

The current built deposit lives at `MEGA/Taxonomy/wlist/package/`. Copy the *kept*
artifacts into `py_proj/wlist/data_package/build/` (CSV/SQL/DDL/DQA/changes PDF — NOT
the `.xlsx`, per ADR-006). Cross-mount, so this is a terminal `cp`, not a Cowork move.
Then `Taxonomy/wlist` reverts to source-data input only.

## Step 5 — Promote the field dictionary + optional formalisation

- `wlist_package.md` → `data_package/DATA_PACKAGE.md` (the deposit's field dictionary +
  provenance).
- Optional: add `datapackage.json` (Frictionless) and/or `CITATION.cff` for a
  spec-conformant, citable deposit (ADR-006). Do before minting the figshare DOI.

## Step 6 — Git remote (when ready)

`wlist` is local-only. Steps in `WORKING_PRACTICES.md` (git novice cheat sheet →
"Pushing a repo to GitHub"). Confirm the ADR-002 credential scrub first
(`git log --oneline | tail -1` = the redacted root commit — already true as of 2026-07-13).

---

## Reference
- Target spec: `strategy/03_wlist_architecture_target.md` (layout §3, data package §4,
  consolidation §5, disposition table §6, staged plan §7).
- Decisions: `strategy/02_wlist_dev_log.md` ADR-004/005/006; ecosystem
  `strategy_ecosystem/01_ecosystem_dev_log.md` D-061 (vocabulary), D-020/D-021 (currency),
  D-015 (DB-access consolidation, deferred), D-060 (survey/sighting join), D12 (wlist
  canonical table, open).
- Env constraint (why this is a hand-off): Cowork FUSE mount blocks `unlink`/`rmdir` and
  cross-mount rename; see project memory `wlist-architecture-review.md`.
