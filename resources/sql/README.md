# wlist SQL resources

Mirrors the `trends` exemplar (`tOccTrends/resources/sql/`) and the ecosystem
currency model (D-020/D-021). Two tiers:

- **`runtime/`** — SQL that defines **deployed** `wlist` database objects (the
  live procedures/DDL that are the *source of truth* for what runs in `dcoredb`),
  and any SQL executed programmatically. Packaged.
- **`ops/`** — one-off, diagnostic, import, and reconciliation SQL run by hand from
  a terminal. **Not** packaged, not a deployed source of truth.

## Classification is not yet done (hand-off)

The files currently in `../../sql/` still need to be classified into `runtime/`
vs `ops/` **against what is actually deployed in `dcoredb`** — this needs live DB
access (Claude Code territory; Cowork cannot reach the DB). Do not guess-move them.

Provisional mapping (verify before moving), from `strategy/03_wlist_architecture_target.md` §6:

**Likely `runtime/`** (deployed objects): `w_add_row.sql`, `w_delete_row.sql`,
`w_is_core.sql`, `w_check_ssp_required.sql`, `wlist_package.sql`, `wlist_ddl.sql`.

**Likely `ops/`** (one-off / diagnostic): `avilist_import.sql`,
`AviList_wlist_integration.sql`, `WLAB.sql`, `WLAB_add taxon and shuffle sort.sql`,
`add or match abd fields to wlist.sql`, `archive_and_update wlist.sql`,
`import and match ala through galah.sql`, `version reconciliation.sql`,
`ds_sensitive_reco.sql`, `w_add_row.sql` variants, `wlist_al_2025.sql`.

Once a `_dev/` or loose object is confirmed deployed, **move its source here**
(promotion rule, D-021).
