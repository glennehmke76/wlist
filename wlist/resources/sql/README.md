# wlist SQL resources

Mirrors the `trends` exemplar (`tOccTrends/resources/sql/`) and the ecosystem
currency model (D-020/D-021). Two tiers:

- **`runtime/`** — SQL that defines **deployed** `wlist` database objects (the
  live procedures/DDL that are the *source of truth* for what runs in `dcoredb`),
  and any SQL executed programmatically. Packaged.
- **`ops/`** — one-off, diagnostic, import, and reconciliation SQL run by hand from
  a terminal. **Not** packaged, not a deployed source of truth.

## Classification done (2026-07-13, Claude Code, verified against live `dcoredb`)

The old flat `../../sql/` folder is retired — its 14 files were checked one by one
against `pg_get_functiondef`/`pg_get_viewdef`/`\d+` output and moved with `git mv`.
See `strategy/02_wlist_dev_log.md` ADR-007 for the full verification trail and the
surprises found (the provisional mapping in `03_wlist_architecture_target.md` §6 was
**not quite right** — see below).

**`runtime/`** (confirmed deployed, body matches live definition exactly):
`w_add_row.sql` (proc `wlist_add_row`), `w_delete_row.sql` (proc `wlist_delete_row`),
`w_is_core.sql` (trigger fn `update_is_core`), `w_check_ssp_required.sql` (trigger fn
`update_ssp_required`).

**`ops/`** (one-off / diagnostic / import / reconciliation, not the deployed source
of truth even where a file's *last* block happens to match a live object — see
surprises): `avilist_import.sql`, `AviList_wlist_integration.sql`, `WLAB.sql`,
`WLAB_add taxon and shuffle sort.sql`, `add or match abd fields to wlist.sql`,
`archive_and_update wlist.sql`, `import and match ala through galah.sql`,
`version reconciliation.sql`, `ds_sensitive_reco.sql`, `wlist_al_2025.sql`.

**`_archive/`** (dead, not `ops/` — corrected from the provisional guess):
`wlist_package.sql` — moved to `_archive/wlist_package.sql`. It is **not** deployed
(no matching function/view/procedure), **not** read by any script (`package_wlist.py`
has its own inline, since-evolved copy of these queries), and its embedded DDL is
stale against the live `wlist` table schema. Superseded, not live — quarantined per
D-020.

**Surprises found during verification (not yet acted on further — see dev log):**
- `wlist_ddl.sql`, named in `wlist_dqa.py`'s `parse_schema_constraints_from_ddl()`
  and listed as "likely runtime" in the target spec, **does not exist anywhere in
  the repo or its history**. `wlist_dqa.py` degrades gracefully (returns `[]`) when
  it's missing, so this has been a silent no-op, not a crash.
- `resources/sql/ops/WLAB.sql` and `resources/sql/ops/ds_sensitive_reco.sql` each
  embed a **currently-live** object (`wlist_sp` view; `ds_sensitive_reco` view,
  respectively) as the last of several iterative/superseded blocks in an otherwise
  scratch/working file. They're filed under `ops/` because that's what the file
  *is* (working history), but this means the live source of truth for those two
  views is not currently a clean canonical file — a candidate follow-up (extract to
  `runtime/`) per the D-020/D-021 promotion rule, not done here to avoid scope creep.
