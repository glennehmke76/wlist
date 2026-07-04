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

---

## Open threads (candidates for future ADRs)

- **`backup.py` vs. `ingest_edited_wlist.py --archive-and-update`'s built-in backup** — possible duplicate/overlapping backup mechanisms; not yet reconciled.
- **`wlist_backup/` (in `applied_projects`, not moved with the package)** — needs a "does this belong in `wlist/_archive/`, or is it a separate backup-tier concern" decision.
- **`sql/wlist_al_2025.sql.bak`** — D-020/D-021 quarantine candidate, not yet actioned.
- **`taxonomy/avilist_wlist_2025/` notebook trio** — looks like a one-off analysis run; candidate for a `demos/`-style home once confirmed (range precedent).
- **DB-object verification** — repo `sql/*.sql` vs. deployed `dcoredb` procedures not yet checked (Claude Code territory — Cowork can't reach the live DB).
- **Ecosystem `D12`** (many parallel `wlist_*` tables in `public`, needs a canonical-table + changelog design) — now squarely this package's remit.
- **Package formalisation** (`pyproject`/`resources/sql/{runtime,ops}` layout matching `sites`/`trends`) — deferred, Track B in `00_strategy.md`.
