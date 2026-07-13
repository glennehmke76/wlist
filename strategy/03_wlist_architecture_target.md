# wlist — Target Architecture (re-architecture review 2.0)

Entry point for the **second** architecture pass on `wlist`, opened 2026-07-13
(Cowork). The first pass (2026-07-05, `00_strategy.md` / `01_wlist_deepdive.md` /
ADR-001–003) promoted `wlist` to a top-level git repo and did the safety/legibility
Track A. This doc defines **Track B — formalisation**: bringing `wlist` into line
with the `trends` domain template now that `trends` is the agreed ecosystem exemplar,
and resolving the terminology and packaging questions Glenn raised.

**Status:** Proposed target + migration plan. Decisions ratified in ADR-004/005/006
(this package) and ecosystem D-061 (vocabulary). Physical migration is staged —
see §7; only the safe, reversible subset is executed from Cowork.

---

## 1. Terminology — one word per thing (ratified)

Three distinct things had been sharing the words *project* / *package*. Fixed
vocabulary, applied ecosystem-wide (see ecosystem **D-061**), locally **ADR-004**:

| Term | Means | Example |
|---|---|---|
| **domain** | A top-level unit of the `py_proj` ecosystem — the conceptual + repo unit that radiates off the hub. | `wlist`, `trends`, `range`, `sites` are the four data domains; `root`, `strategy_ecosystem` are the governance/substrate domains. |
| **package** | The importable/versioned **code** inside a domain (the git repo's working tree). | the `wlist` code package at `py_proj/wlist`. Reserved for code — *not* the figshare deposit. |
| **data package** | The outward-facing, **citable published artifact** — the figshare deposit built from the domain's data. | the `wlist` **data package** (CSV + SQL + DDL + DQA report + change table), figshare-deposited, DOI on finalisation. |

"project" is **retired** as a structural term (it survives only in loose prose like
"this engagement"). Where old docs say "the wlist package" meaning the figshare
deposit, read "**data package**".

## 2. The exemplar — what `trends` looks like (target to mirror)

```
trends/                         # domain repo root
  pyproject.toml  MANIFEST.in  README.md
  tOccTrends/                   # the code PACKAGE (importable)
    __init__.py  orchestration/  core/  render/
    resources/
      sql/
        runtime/                # SQL executed by Python, packaged (source of truth for deployed objects)
        ops/                    # terminal/diagnostic SQL, NOT packaged
  strategy/                     # 00_strategy, 01_deepdive, 02_dev_log, NN_specs
  _dev/                         # in-development, not yet promoted
  _archive/                     # quarantined dead code (never swept)
  tests/  tools/  documentation/  context/
```

Two structural rules carried over (ecosystem D-020/D-021): `resources/sql/{runtime,ops}`
is the deployed source of truth; `_archive/` is quarantine and is never modified or
swept.

## 3. Target `wlist` layout

```
wlist/                          # domain repo root (py_proj/wlist) — CONSOLIDATED home
  pyproject.toml  MANIFEST.in  README.md   [pyproject/MANIFEST = new]
  wlist/                        # the code PACKAGE (rename of loose root scripts into a package)
    __init__.py
    core/                       # db connection + shared helpers (get_db_connection extracted here)
    ingest/                     # ingest_edited_wlist.py, validate_wlist_update.py
    build/                      # package_wlist.py, export_avilist_change_table.py, wlist_dqa.py  (data-package builders)
    tools/                      # internal-only utilities NOT part of the data package
                                #   export_wlist_extended.py (xlsx), find_unmatched_taxon_ids.py, backup.py
    add_taxon/                  # self-contained mini-workflow (as-is)
    resources/
      sql/
        runtime/                # deployed wlist DB objects: w_add_row, w_delete_row, w_is_core,
                                #   w_check_ssp_required, wlist_package.sql, wlist_ddl.sql
        ops/                    # one-off / diagnostic: avilist_import, AviList_wlist_integration,
                                #   WLAB*, version reconciliation, ds_sensitive_reco, import-and-match
  data_package/                 # the CITABLE deposit (built artifacts + figshare tooling)
    build/ (or dist/)           # generated CSV/SQL/DDL/DQA/PDF  ← OUTPUT_DIR retargets here
    figshare/                   # figshare_create_draft.py, figshare_submit.py, FIGSHARE_SUBMIT_README.md
    DATA_PACKAGE.md             # spec: what's in the deposit, field dictionary (ex-wlist_package.md)
  reconciliation/               # local working folder (AviList change-class): keep, but see §6
  taxonomy/                     # avilist_wlist_2025 reconciliation notebooks (as-is; demos/ candidate)
  strategy/                     # 00, 01, 02, 03 (this doc), NN specs
  _dev/  _archive/  tests/  documentation/  context/
```

Key differences from today: (a) loose root scripts become a real **code package**
(`wlist/wlist/…`) split by role — ingest / build / tools / core; (b) SQL rationalised
into `resources/sql/{runtime,ops}`; (c) a first-class **`data_package/`** separating
the citable deposit and its figshare tooling from the code that builds it; (d)
`pyproject.toml` + `MANIFEST.in` added to match the exemplar.

## 4. The data package — what it is and what belongs

The data package is the **scientific deposit**, not a code dump. Membership rule:

**In** (portable, open, reproducible): `wlist_core.csv`, `lut_rli.csv`,
`avilist_changes.csv`, `wlist_core.sql`, `wlist.ddl`, `wlist_dqa_report.md`, the
AviList changes PDF, and a `DATA_PACKAGE.md` (field dictionary + provenance, promoted
from `wlist_package.md`). Consider a machine-readable `datapackage.json`
(Frictionless Data) or a `CITATION.cff` for a more formal, spec-conformant deposit —
cheap to add, improves citability.

**Out** (internal only, not deposited): `export_wlist_extended.py`'s **`.xlsx`**
outputs — Excel isn't an archival scientific format; keep the CSV (`wlist_extended.csv`)
if a wide export is wanted for the deposit, drop the xlsx. `backup.py`,
`find_unmatched_taxon_ids.py`, and the reconciliation working files are tooling/scratch,
not deposit content.

## 5. The two-location contract (consolidation)

Decision (ADR-005): **consolidate into `py_proj/wlist`**. Today `OUTPUT_DIR` in
`package_wlist.py` and `export_avilist_change_table.py` is hardcoded to
`MEGA/Taxonomy/wlist/package`, and `figshare_submit.py` resolves `FILES` relative to
its own folder — so the built deposit lives outside the repo. Target:

- `OUTPUT_DIR` → `wlist/data_package/build/` (inside the repo, git-tracked or
  git-ignored per §7 note).
- `Taxonomy/wlist` reverts to **source-data input only** (AviList working xlsx,
  `wlist.drawio`, scratch) — no longer the build sink.
- `figshare_submit.py`'s `PACKAGE_DIR` points at `data_package/build/`, collapsing the
  ADR-003 "edit here, run there" split.

This is a **code edit that changes where outputs land** — deliberately staged (§7),
not auto-applied, so nothing downstream that reads `Taxonomy/wlist/package` breaks
silently.

## 6. Disposition of the loose / uncertain files

| Item | Disposition | Confidence |
|---|---|---|
| `package_wlist.py`, `export_avilist_change_table.py`, `wlist_dqa.py` | → `wlist/build/` (data-package builders) | high |
| `ingest_edited_wlist.py`, `validate_wlist_update.py` | → `wlist/ingest/` | high |
| `export_wlist_extended.py` (xlsx) | → `wlist/tools/`; xlsx **excluded** from deposit | high |
| `find_unmatched_taxon_ids.py`, `backup.py` | → `wlist/tools/` | high |
| `get_db_connection` (in `package_wlist.py`) | extract → `wlist/core/`; consolidate onto `sys_py` connector (ties to D-015 deferred) | med |
| `sql/*` core procedures (`w_*`, `wlist_package.sql`, `wlist_ddl.sql`) | → `resources/sql/runtime/` | **needs DB verify** |
| `sql/*` import/reconciliation one-offs | → `resources/sql/ops/` | **needs DB verify** |
| `sql/wlist_al_2025.sql.bak` | → `_archive/` (D-020 quarantine) | high — **done this session** |
| `reconciliation/` | keep as working folder; confirm outputs vs deposit boundary | med |
| `taxonomy/avilist_wlist_2025/` notebooks | `demos/`-style home (range precedent) once confirmed one-off | med |
| `wlist_backup/` (left in `applied_projects`) | reconcile vs `backup.py`; decide `_archive/` vs backup-tier | open |

Everything marked **needs DB verify** is a runtime-vs-ops classification that requires
checking what's actually deployed in `dcoredb` — **Claude Code territory** (Cowork
can't reach the DB). Do not guess-move these; the `resources/sql/{runtime,ops}`
skeleton + this table is the hand-off.

## 7. Migration plan — staged by capability

**A. Safe now (Cowork, this session) — additive + `git mv` only, reversible:**
1. Create `resources/sql/{runtime,ops}/` + `README.md` (classification policy).
2. Create `_archive/`; `git mv sql/wlist_al_2025.sql.bak _archive/`.
3. Record ADR-004/005/006 + ecosystem D-061.

**B. Needs your terminal (deletes / cross-mount) or Claude Code (DB):**
4. Retarget `OUTPUT_DIR` → `data_package/build/` and `figshare_submit.py` `PACKAGE_DIR`
   (code edit; test a dry build).
5. Classify + `git mv` each `sql/*` into `runtime/` vs `ops/` (verify against deployed
   `dcoredb` objects first).
6. Refactor loose root scripts into the `wlist/` code package (`core/ingest/build/tools`);
   add `pyproject.toml` + `MANIFEST.in`; fix the `wlist_dqa.py` → `wlist_ddl.sql`
   relative path after the move.
7. Consolidate build outputs from `Taxonomy/wlist/package` into `data_package/build/`
   (cross-mount copy — your terminal).
8. Add `datapackage.json` / `CITATION.cff` to the deposit (optional formalisation).

**Git remote (novice steps, when ready):** `wlist` is a local repo (`master`), no
remote. Mirror the `range` pattern (GitHub). Copy-paste flow:
```
cd ~/MEGA/py_proj/wlist
# create an EMPTY repo named 'wlist' on github.com first (no README/licence)
git remote add github https://github.com/glennehmke76/wlist.git
git push -u github master        # confirm: `git remote -v` then `git log github/master`
```
Confirm the credential-history scrub (ADR-002) is done **before** the first push —
`git log --oneline | tail -1` should be the redacted root commit, which it now is.

## 8. Cross-links

- Ecosystem exemplar + register: `../../strategy_ecosystem/00_ecosystem_map.md` §5;
  vocabulary decision `../../strategy_ecosystem/01_ecosystem_dev_log.md` **D-061**.
- Currency model (runtime/ops/_dev/_archive): ecosystem D-020/D-021.
- DB-access consolidation (deferred): ecosystem D-015.
- `wlist` canonical-table/changelog question: ecosystem D12 (still open, this domain's remit).
- This package: `00_strategy.md` (Track B is what this doc executes), `02_wlist_dev_log.md`
  ADR-004/005/006.
```
