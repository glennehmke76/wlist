# wlist — Development Decision Log

A **strategic record of logic and decision-making** for the `wlist` package. The *why*, tracked over time — distinct from the operational `README.md` (the *how*, current state). Mirrors the pattern in `range/strategy/02_range_dev_log.md`, `sites/strategy/02_sites_dev_log.md`, `trends/strategy/02_trends_dev_log.md`.

**Status:** Seeded 2026-07-05 (Cowork) the same session `wlist` was promoted to a top-level package and git-initialised (ecosystem `D-023`). This is the start of an active architecture review — unlike `range`'s light-touch pass, Glenn intends to develop this further.

**Format:** ADR-style, numbered, dated, **append-only**. Change of thinking → new entry that supersedes (mark the old `Superseded by ADR-NNN`); don't rewrite. Project decisions use `ADR-`; when a decision is a local application of an ecosystem one, **link up** to the `D-` entry rather than restating it.

### ADR entry template

```
## ADR-NNN — <short title>
- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by ADR-NNN | Deprecated
- **Context:** what prompted this; the problem/constraint.
- **Decision:** what was decided.
- **Rationale:** why; technical basis.
- **Consequences:** follow-on effects, migrations, consumers to update.
- **Links:** code, ecosystem D-numbers, related docs.
```

### Implementation status

| # | Decision | Status |
|---|---|---|
| ADR-001 | Promote to top-level package + `git init` | Done |
| ADR-002 | Hardcoded DB password — redact + rotate? | Redacted in files (Done); **history scrub still needed from Glenn's own terminal** |
| ADR-003 | `figshare_submit.py` cross-location gap | Done |
| ADR-004 | Terminology: domain / package / data package | Accepted (links up to ecosystem D-061) |
| ADR-005 | Consolidate into `py_proj/wlist`; adopt trends target layout | Done — executed 2026-07-13 (Claude Code, Track B) |
| ADR-006 | Formalise the figshare **data package** | Done — `data_package/` structure executed 2026-07-13 |
| ADR-007 | Track B execution: SQL classification, code package refactor, `OUTPUT_DIR` retarget | Done — all steps complete (2026-07-13/14); pushed to GitHub `main` |

---

## ADR-001 — Promote `wlist` to top-level package; `git init`

- **Date:** 2026-07-05
- **Status:** Accepted — executed 2026-07-05 (Cowork).
- **Context:** Applies ecosystem **`D-023`** directly (see `../../strategy_ecosystem/01_ecosystem_dev_log.md`) — `wlist` sat nested at `wdb/wlist`, sharing a folder with unrelated applied-analysis projects, and was never independently versioned despite carrying a figshare DOI commitment. Glenn confirmed: promote to top-level, own git repo; nest `taxonomy/` inside it; rename the residual folder to `applied_projects`.
- **Decision:** Moved `wdb/wlist` → `py_proj/wlist`; moved `wdb/taxonomy` → `py_proj/wlist/taxonomy`; `git init` in `wlist` only (root-commit `cc70263`, branch `master`, 46 files); added a `.gitignore` (`__pycache__/`, `.DS_Store`, `.ipynb_checkpoints/`, `*.log`, etc.). `wdb` renamed to `applied_projects` separately (ecosystem-level, not this package's concern).
- **Rationale:** matches `range`/`sites`/`trends` precedent; this package's figshare/versioning commitments don't share a lifecycle with the applied-analysis folders it used to sit beside. See `D-023` for the full ecosystem-level reasoning.
- **Consequences:** `wlist_backup/` (old dated backup snapshot) was **not** moved — it's still in `applied_projects`, pending reconciliation with `backup.py`'s own behaviour (open thread below). Import paths between `taxonomy/` and the rest of `wlist` not yet checked. This scaffold (`00_strategy.md`, this log, `01_wlist_deepdive.md`) created in the same pass, per the playbook's new-package scaffold — see `00_strategy.md` for the wlist-specific goals this sets up.
- **Links:** ecosystem `D-023`; `00_strategy.md`; `01_wlist_deepdive.md`.

## ADR-002 — Hardcoded default DB password across `wlist` (mirrors ecosystem `D1`)

- **Date:** 2026-07-05
- **Status:** Accepted — **option 2 executed 2026-07-05 (Cowork).** Git-history scrub still outstanding (see Consequences — needs Glenn, from his own terminal).
- **Context:** The Phase-1 inventory (`01_wlist_deepdive.md` §3) found a literal default password (`os.getenv("DCORE_PASSWORD", "<redacted>")`, with matching default host/user/db) hardcoded in `package_wlist.py` and `wlist_dqa.py`, and **documented in plaintext** in `README.md`, `add_taxon/README.md`, and `wlist_package.md`. This is the exact class of issue the ecosystem log already flagged for `sys_py/config.py` (`D1`: "no hardcoded credentials... scrub from git history before any push"). Because `wlist` was just `git init`'d, this password was sitting in the **root commit** of a brand-new repo — but that repo has **no remote configured and has not been pushed anywhere**, so the exposure so far is local-disk only.
- **Options considered:**
  1. Leave as-is until the next active session, redact then.
  2. Redact now (replace the hardcoded fallback with `password=None`/no-default → falls back to `~/.pgpass`, matching the pattern already adopted by the live `trends`/`range`/`sites` pipelines per the ecosystem D-001 job-lot notes).
  3. Redact **and** rotate the actual `dcoredb` password.
- **Decision:** **Option 2** (Glenn, 2026-07-05). Rotation (option 3) not actioned — Glenn's call to leave for now.
- **Rationale:** matches the ecosystem-adopted pattern (env/`.env`/`~/.pgpass`, no hardcoded secret); the sandbox environment this session ran in **cannot delete files**, which ruled out amending/rewriting git history from here (see Consequences) — redacting the *current* files was the achievable part.
- **Result (2026-07-05):** Redacted in code: `package_wlist.py` `get_db_connection()` and its `password = os.getenv("DCORE_PASSWORD", ...)` internal helper, and `wlist_dqa.py`'s `--password` argparse default — all now have **no hardcoded fallback** (`os.getenv("DCORE_PASSWORD")`/empty string only). Redacted in docs: `README.md`, `add_taxon/README.md`, `wlist_package.md` no longer print the literal value. Committed as a follow-up commit.
- **Consequences — 🔴 not fully closed:** the literal password string **still exists in this repo's git history** (blob content of the root commit `cc70263`). This Cowork sandbox discovered it **cannot delete files** on the MEGA-mounted folder (`rm`/`unlink` return `Operation not permitted` even for brand-new dummy files — see the environment note in project memory `wlist-architecture-review.md`), which rules out `git rebase`/`filter-branch`-style history rewriting from here (those need to delete/replace refs and objects). **Glenn: run this from your own terminal to actually remove the password from history** (safe — this repo has no remote, so nothing has been shared yet):
  ```
  cd ~/MEGA/py_proj/wlist
  rm -rf .git
  git init
  git add -A
  git commit -m "Initial commit: wlist as top-level package (D-023), credentials redacted"
  ```
  This discards the two trivial local commits and starts one clean commit from the current (already-redacted) files — simplest option since nothing was ever pushed. Confirm `~/.pgpass` has a working `dcoredb` entry first, since the scripts now rely on it rather than the old hardcoded fallback.
- **Links:** ecosystem `D1`; `01_wlist_deepdive.md` §3 finding 1; `package_wlist.py`, `wlist_dqa.py`, `README.md`, `add_taxon/README.md`, `wlist_package.md`; project memory `wlist-architecture-review.md`.

## ADR-003 — `figshare_submit.py` exists only in the Cowork data workspace, not this repo

- **Date:** 2026-07-05
- **Status:** Accepted — executed 2026-07-05 (Cowork).
- **Context:** `package/figshare_create_draft.py` is a thin wrapper that hard-requires a sibling `figshare_submit.py` (`Path(__file__).with_name("figshare_submit.py")`, errors if missing). That file did not exist in `py_proj/wlist/package/` — it existed only at `MEGA/Taxonomy/wlist/package/figshare_submit.py`, the Cowork data/docs workspace (a separate physical location from this code repo, kept deliberately distinct per `00_strategy.md` §2). The figshare packaging workflow therefore only worked by accident of both locations coexisting on Glenn's machine — not reproducible from this repo alone.
- **Options considered:**
  1. Copy `figshare_submit.py` into `py_proj/wlist/package/` (now the canonical, versioned source) and treat the copy in `Taxonomy/wlist` as a non-canonical run-time mirror.
  2. Leave the split as-is, documenting it explicitly as a known dependency rather than fixing it.
  3. Point `figshare_create_draft.py` at the `Taxonomy/wlist` location explicitly (env var or config), formalising the split rather than collapsing it.
- **Decision:** **Option 1** (Glenn, 2026-07-05).
- **Rationale:** the packaging script is source code and belongs in the versioned repo; `Taxonomy/wlist` should hold data/outputs (and, pragmatically, a run-time mirror of the script — see Consequences), not the only copy of a script the code repo depends on.
- **Result (2026-07-05):** `figshare_submit.py` copied byte-for-byte into `py_proj/wlist/package/` (confirmed no hardcoded secrets in it — token is read from `FIGSHARE_TOKEN` env var only). `FIGSHARE_SUBMIT_README.md` updated with a note explaining where to actually run it from (see Consequences).
- **Consequences — one nuance, not fully collapsed:** `figshare_submit.py` resolves its `FILES` list relative to its own folder (`PACKAGE_DIR = Path(__file__).parent`), and the actual **built data outputs** (`wlist_core.csv`, the PDF, DQA report, etc. — produced by `package_wlist.py`'s hardcoded `OUTPUT_DIR`) live in `MEGA/Taxonomy/wlist/package/`, not in this git repo. So this repo's copy is the one to **edit**, but to actually **run** a submission, sync the edited file to `Taxonomy/wlist/package/figshare_submit.py` first (documented in `FIGSHARE_SUBMIT_README.md`). Not collapsing this further (e.g. making `PACKAGE_DIR` configurable) was a deliberate scope call — bigger change than "fix the missing file".
- **Links:** `01_wlist_deepdive.md` §3 finding 2; `package/FIGSHARE_SUBMIT_README.md`; project memory `figshare-wlist-submission.md`.

## ADR-004 — Terminology: **domain** / **package** / **data package**

- **Date:** 2026-07-13
- **Status:** Accepted (Glenn, this session). Links **up** to ecosystem **D-061**.
- **Context:** "project", "package", and "the wlist package" were being used
  interchangeably for three different things — the top-level ecosystem unit, the
  importable code, and the figshare deposit. The doc architecture already leans on
  "domain" (`domain_relationships.md`, `by_domain/`), but prose mixed in "project"
  and overloaded "package".
- **Decision:** Fix one word per thing: **domain** = top-level ecosystem unit
  (`wlist`, `trends`, `range`, `sites`); **package** = the importable/versioned code
  inside a domain; **data package** = the outward-facing citable figshare deposit.
  "project" retired as a structural term.
- **Rationale:** removes the collision Glenn flagged; "data package" is the standard
  scientific-repository framing and cleanly separates the deposit from the code that
  builds it. This is ecosystem-wide vocabulary, hence ratified at ecosystem level
  (D-061) and merely applied here.
- **Consequences:** `wlist_package.md` → promote to `data_package/DATA_PACKAGE.md`;
  read legacy "wlist package" (deposit sense) as "data package". No code impact.
- **Links:** ecosystem D-061; `03_wlist_architecture_target.md` §1.

## ADR-005 — Consolidate into `py_proj/wlist`; adopt the `trends` target layout

- **Date:** 2026-07-13
- **Status:** Accepted (Glenn, this session). Skeleton executed; code/data moves staged.
- **Context:** `trends` is now the agreed ecosystem exemplar. `wlist`'s code side is
  loose (standalone scripts at repo root, a flat un-rationalised `sql/`), and its build
  outputs live in a *different tree* (`Taxonomy/wlist/package`, via hardcoded
  `OUTPUT_DIR`) from the code — a split that only works by both locations coexisting.
- **Decision:** Mirror the `trends` layout (`resources/sql/{runtime,ops}`, a real code
  package split by role, `_dev/`/`_archive/`, `pyproject`/`MANIFEST`) and **consolidate
  the working home into `py_proj/wlist`**: `OUTPUT_DIR` retargets to
  `data_package/build/` inside the repo; `Taxonomy/wlist` reverts to source-data input
  only. Full target in `03_wlist_architecture_target.md` §3/§5.
- **Rationale:** one versioned tree; matches the exemplar; collapses the ADR-003
  "edit here, run there" figshare split.
- **Consequences — staged by capability:** *Safe now (Cowork, done):*
  `resources/sql/{runtime,ops}/` + README skeleton created; `_archive/` created and
  `sql/wlist_al_2025.sql.bak` moved there (D-020 quarantine). *Deferred (needs terminal
  deletes/cross-mount or Claude Code DB access):* classify each `sql/*` into
  runtime/ops against deployed `dcoredb`; refactor root scripts into the `wlist/` code
  package (fix `wlist_dqa.py`→`wlist_ddl.sql` relative path post-move); retarget
  `OUTPUT_DIR`; copy built outputs across from `Taxonomy/wlist`. **Env constraint noted:**
  this Cowork mount blocks `unlink`/`rmdir` (FUSE guard) and can't rename across mounts,
  so relocations here use `git mv` only and cross-mount/delete steps are handed to Glenn.
- **Links:** ecosystem D-020/D-021, D-015; `00_strategy.md` §4 Track B;
  `03_wlist_architecture_target.md` §3/§6/§7.

## ADR-006 — Formalise the figshare **data package**

- **Date:** 2026-07-13
- **Status:** Accepted (Glenn, this session). Membership rule set; structure staged.
- **Context:** The deposit has no DOI yet and isn't finalised, so its structure is
  still open to change. Currently it's whatever `package_wlist.py` dumps into
  `Taxonomy/wlist/package`, mixed with Excel exports that don't belong in a scientific
  repository.
- **Decision:** Give the data package a first-class home (`data_package/` with
  `build/` artifacts, `figshare/` tooling, `DATA_PACKAGE.md` field dictionary) and a
  **membership rule**: portable/open/reproducible artifacts in (CSV, SQL, DDL, DQA
  report, changes PDF, field dictionary); internal/Excel/scratch out. `.xlsx` exports
  (`export_wlist_extended.py`) are excluded from the deposit — keep the CSV equivalent
  if a wide export is wanted. Optionally add `datapackage.json` (Frictionless) and/or
  `CITATION.cff` for a spec-conformant, citable deposit.
- **Rationale:** Excel isn't an archival format; a clear membership rule + machine-readable
  metadata makes the deposit properly citable and separates deposit content from build tooling.
- **Consequences:** `export_wlist_extended.py` reclassified as an internal tool;
  `wlist_package.md` becomes `DATA_PACKAGE.md`; figshare tooling (ADR-003) moves under
  `data_package/figshare/`. Do before finalising the DOI.
- **Links:** project memory `figshare-wlist-submission.md`; ADR-003;
  `03_wlist_architecture_target.md` §4.

---

## ADR-007 — Track B execution: SQL classification, code package refactor, `OUTPUT_DIR` retarget

- **Date:** 2026-07-13
- **Status:** Accepted, executed (Claude Code, this session — hand-off
  `strategy/_handoffs/20260713_wlist_rearch_trackB_HANDOFF.md`). Steps 1–3 and 5 done
  in full; step 4 (cross-mount copy of existing built outputs) and step 6 (git remote)
  remain for Glenn's terminal — Cowork's FUSE mount blocks `unlink`/`rmdir` and this
  sandbox has no `dcoredb` access, so cross-mount/deletes and DB verification were the
  reason for the hand-off in the first place.
- **Context:** ADR-005/006 set the target layout and data-package structure but staged
  the DB-dependent and terminal-dependent steps. This entry records what was actually
  found and done when those steps were executed against the live `dcoredb`.

- **Step 1 — SQL classification (verified against live `dcoredb`):**
  - Confirmed deployed, moved to `resources/sql/runtime/`: `w_add_row.sql` (proc
    `wlist_add_row`), `w_delete_row.sql` (proc `wlist_delete_row`), `w_is_core.sql`
    (trigger fn `update_is_core`), `w_check_ssp_required.sql` (trigger fn
    `update_ssp_required`) — all four bodies matched `pg_get_functiondef` exactly.
  - Moved to `resources/sql/ops/` (one-off/diagnostic/import/reconciliation, not the
    deployed source of truth): `avilist_import.sql`, `AviList_wlist_integration.sql`,
    `WLAB.sql`, `WLAB_add taxon and shuffle sort.sql`, `add or match abd fields to
    wlist.sql`, `archive_and_update wlist.sql`, `import and match ala through
    galah.sql`, `version reconciliation.sql`, `ds_sensitive_reco.sql`,
    `wlist_al_2025.sql`.
  - **Correction to the provisional mapping:** `wlist_package.sql` was guessed
    "likely runtime" in `03_wlist_architecture_target.md` §6 but is actually **dead** —
    moved to `_archive/wlist_package.sql` instead. It is not deployed (no matching
    function/view), not read by any script (`package_wlist.py` has its own inline,
    since-evolved copy of the same queries), and its embedded DDL is stale against the
    live `wlist` table (missing ~20 columns added since, e.g. `bird_sub_group`,
    `is_coastal`, `ssp_required`).
  - **Surprises (not actioned further, flagged for a future pass):**
    (a) `wlist_ddl.sql`, named in `wlist_dqa.py` and listed as "likely runtime" in the
    target spec, does not exist anywhere in the repo or its history — `wlist_dqa.py`
    silently returns `[]` when it's missing, so this has been a no-op, not a crash.
    (b) `resources/sql/ops/WLAB.sql` and `resources/sql/ops/ds_sensitive_reco.sql` each
    embed a **currently-live** view (`wlist_sp`; `ds_sensitive_reco`) as the last of
    several superseded iterations in an otherwise scratch file — the live source of
    truth for those two views isn't a clean canonical file. Candidate follow-up:
    extract to `runtime/` per the D-020/D-021 promotion rule. Not done here (scope).
  - See `resources/sql/README.md` for the full classification writeup.

- **Step 2 — code package refactor:** Created `wlist/wlist/{core,ingest,build,tools}/`
  + `__init__.py`s; moved `add_taxon/` and `resources/` inside `wlist/wlist/`. Extracted
  `get_db_connection` (previously duplicated/imported from `package_wlist.py`) into
  `wlist/wlist/core/db.py`; `package_wlist.py` now imports it rather than defining its
  own copy. Did **not** consolidate onto a `sys_py` shared connector (D-015) — checked,
  and no `sys_py` package with a ready connector currently exists in the ecosystem to
  consolidate onto; still deferred. Fixed cross-module imports broken by the
  ingest/build/tools split (e.g. `export_wlist_extended.py` and
  `find_unmatched_taxon_ids.py` importing `package_wlist` across the new package
  boundary). Fixed `wlist_dqa.py`'s DDL parser path to point at
  `resources/sql/runtime/wlist_ddl.sql` (per the hand-off) — though per the Step 1
  surprise, that file doesn't exist yet, so this is a path fix, not a functional one.
  **Found and fixed one coupling the hand-off didn't call out:** `wlist/tools/backup.py`
  computed its backup source folder as `Path(__file__).resolve().parent`, which was
  correct when `backup.py` lived at the repo root but silently pointed at the wrong
  folder (and would have failed its own sanity check) once moved three levels deeper
  into `wlist/tools/`. Fixed to `.parents[2]` (domain repo root) and updated the sanity
  check's expected marker file for the new layout; verified with `--dry-run`. Verified
  every moved module still imports and a live `get_db_connection()` query succeeds.
  Added `pyproject.toml` + `MANIFEST.in` mirroring `trends`.

- **Step 3 — `OUTPUT_DIR` retarget:** `package_wlist.py` and
  `export_avilist_change_table.py`'s `OUTPUT_DIR` now resolve to
  `<domain repo root>/data_package/build/` (computed from `__file__`, not hard-coded).
  `figshare_submit.py`'s `PACKAGE_DIR` now points at `data_package/build/` (a sibling of
  `data_package/figshare/`, where the script itself now lives) instead of its own
  folder — collapsing the ADR-003 split. Ran an actual (not simulated) build via
  `python -m wlist.build.package_wlist` against live `dcoredb`: fetched 1,740 core
  rows, 6 RLI categories, 139 Avilist changes, and wrote `wlist_core.csv`,
  `lut_rli.csv`, `avilist_changes.csv`, `wlist_core.sql`, `wlist.ddl`, and
  `wlist_dqa_report.md` into `data_package/build/` — confirmed inside the repo.
  **Decision:** `data_package/build/` is git-ignored (generated, reproducible from
  `dcoredb`); only a `.gitkeep` and the figshare tooling under `data_package/figshare/`
  are tracked.
  **Surprise found comparing against the actual existing deposit:** the real figshare
  `FILES` list in `figshare_submit.py` includes several items that are **not**
  generated by `package_wlist.py` and existed only as hand-authored files in
  `Taxonomy/wlist/package/` — a deposit-facing `README.md` (with version/DOI/license
  header, distinct from this repo's `README.md` and from `DATA_PACKAGE.md`), `A
  working list of Australian birds.pdf`/`.docx`, `wlist_core_data_dictionary.csv`, and
  `wlist_lut_rli_data_dictionary.csv`. These are curated, not reproducible by re-running
  the build.

- **Step 4 (partial) — Glenn copied the curated deposit files** into `data_package/`
  (tracked, not the git-ignored `build/`): `README_figshare.md` (renamed from
  `README.md` to avoid clashing with the repo/code-package READMEs), `A working list of
  Australian birds.pdf`, `wlist_core_data_dictionary.csv`,
  `wlist_lut_rli_data_dictionary.csv`. **Follow-up fix (Claude Code):**
  `figshare_submit.py`'s `FILES` loop previously resolved every filename under a single
  `PACKAGE_DIR`, which broke once curated files and generated files lived in different
  folders. Replaced with `BUILD_DIR` (generated) + `DATA_PACKAGE_DIR` (curated) plus a
  `CURATED_FILES` name-mapping dict and a `resolve_file()` helper so both `dry_run()`
  and `create_and_upload()` find the right file regardless of which folder it's in.
  Verified: ran `python -m wlist.build.export_avilist_change_table` (the one generated
  file not yet built) and then `dry_run()` — all 11 files in `FILES` resolve and show
  correct sizes (2.2 MB total). Remaining from Step 4: cross-mount `.xlsx`/`.docx`/
  `add_taxon/`/`requirements.txt` copies in `Taxonomy/wlist/package/` were deliberately
  **not** brought across (superseded or excluded per ADR-006) — worth a final glance
  from Glenn to confirm nothing else in that folder needs preserving before it reverts
  to source-data-only per ADR-005.

- **Step 5 — data package field dictionary:** `wlist_package.md` → `git mv`'d to
  `data_package/DATA_PACKAGE.md`; updated its stale path references (old `OUTPUT_DIR`,
  `python -m wlist.package_wlist` → `wlist.build.package_wlist`) and added the
  `wlist_ddl.sql`-doesn't-exist note from Step 1.

- **Step 6 — git remote (Glenn's terminal, 2026-07-14):** `wlist-trackB` merged into
  `master` (merge commit `9028556`), then pushed. GitHub's repo wasn't actually empty
  as the original hand-off assumed — it had a stray `main` branch (one "Add files via
  upload" commit, 3 older SQL variants unconnected to local history), and GitHub
  refuses to delete a repo's default branch via `git push --delete`. Resolved with
  `git push github master:main --force` instead (same end result Glenn had already
  approved — main's content replaced by master's — without needing the delete step).
  `master` now tracks `github/main`. `wlist` is no longer local-only; update any future
  references in `WORKING_PRACTICES.md`'s per-package git state note accordingly.

- **Consequences:** the domain repo (`py_proj/wlist`) is now internally consistent with
  the `trends` exemplar layout end-to-end for everything Claude Code could verify/run.
  Steps 4 (copy real built outputs + curated deposit files across from
  `Taxonomy/wlist/package/`, terminal `cp`) and 6 (git remote push) remain — both need
  Glenn's terminal per the original hand-off's env constraint.
- **Links:** ADR-004/005/006; ecosystem D-020/D-021 (currency), D-015 (DB-access
  consolidation, still deferred — no `sys_py` connector exists yet to consolidate onto);
  `resources/sql/README.md`; `03_wlist_architecture_target.md` §6/§7;
  `strategy/_handoffs/20260713_wlist_rearch_trackB_HANDOFF.md`.

---

## Open threads (candidates for future ADRs)

- **`backup.py` vs. `ingest_edited_wlist.py --archive-and-update`'s built-in backup** — possible duplicate/overlapping backup mechanisms; not yet reconciled.
- **`wlist_backup/` (in `applied_projects`, not moved with the package)** — needs a "does this belong in `wlist/_archive/`, or is it a separate backup-tier concern" decision.
- **`sql/wlist_al_2025.sql.bak`** — D-020/D-021 quarantine candidate, not yet actioned.
- **`taxonomy/avilist_wlist_2025/` notebook trio** — looks like a one-off analysis run; candidate for a `demos/`-style home once confirmed (range precedent).
- ~~**DB-object verification**~~ — done, ADR-007 (2026-07-13).
- **Ecosystem `D12`** (many parallel `wlist_*` tables in `public`, needs a canonical-table + changelog design) — now squarely this package's remit.
- ~~**Package formalisation**~~ — done, ADR-007 (2026-07-13).
- **`wlist_ddl.sql` doesn't exist** (ADR-007) — `wlist_dqa.py` and `DATA_PACKAGE.md` both
  reference it as a repository DDL source file; it's never existed. Either author it
  from the live `wlist`/`lut_rli` schema and promote it to `resources/sql/runtime/`, or
  update the docs/parser to stop implying it does.
- **Extract `wlist_sp` and `ds_sensitive_reco` to clean `runtime/` sources** (ADR-007) —
  both are currently-deployed views whose only source is the last of several
  superseded iterations inside otherwise-scratch `ops/` files (`WLAB.sql`,
  `ds_sensitive_reco.sql`). D-020/D-021 promotion rule candidate.
- ~~**Deposit content split: curated vs. generated**~~ — resolved, ADR-007 (2026-07-13):
  curated files now live tracked under `data_package/` (`README_figshare.md`, the PDF,
  two data-dictionary CSVs); `figshare_submit.py` resolves each `FILES` entry to the
  right folder via `resolve_file()`. Still open: the `.docx` source of the PDF and
  whether `requirements.txt`/`add_taxon/` remnants in `Taxonomy/wlist/package/` need
  preserving before that folder reverts to source-data-only.
