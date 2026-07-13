wlist data package — field dictionary and provenance (DATA_PACKAGE.md)

Promoted 2026-07-13 from `wlist_package.md` per ADR-004/006 (vocabulary: this is
the **data package** field dictionary, not the code **package**).

Overview
- This document describes the outputs produced by wlist/build/package_wlist.py. The script exports three CSV files and a single SQL dump containing CREATE TABLE and INSERT statements.
- Intent: provide simple, portable extracts for sharing and downstream use without requiring access to the operational database.

How to run
- Ensure database environment variables are set as needed (defaults in parentheses):
  - DCORE_HOST (localhost)
  - DCORE_DB (dcoredb)
  - DCORE_USER (glennehmke)
  - DCORE_PASSWORD (no default — set via env var or `~/.pgpass`)
  - DCORE_PORT (5432)
- Then run:
  - python -m wlist.build.package_wlist

Output location and files
- Base output directory: data_package/build/ (in this repo — ADR-005; retargeted from
  the former hard-coded out-of-repo /Users/glennehmke/MEGA/Taxonomy/wlist/package)
  - wlist_core.csv
  - lut_rli.csv
  - avilist_changes.csv
  - wlist_core.sql
  - wlist.ddl (see "Known gap" note below — not actually copied from a repo source file)
- Note: If you change OUTPUT_DIR in package_wlist.py, paths will update accordingly.
- Generated build outputs are git-ignored (see `.gitignore`); this document and the
  figshare tooling under `data_package/figshare/` are what's tracked in git.

Known gap (found verifying ADR-007, not yet resolved)
- This document (and `wlist_dqa.py`'s DDL parser) both refer to a repository source
  file `resources/sql/runtime/wlist_ddl.sql` — it does not exist anywhere in the repo
  or its history. `export_schema_ddl()` in `package_wlist.py` generates the `wlist.ddl`
  build artifact from a hard-coded `WLIST_DDL` string inside that script, not from a
  checked-in source file — so the build still works, but "copy of repository DDL"
  below is aspirational, not an actual file yet.

Data integrity controls in the outputs
- Primary keys
  - The SQL dump defines a primary key on public.wlist(taxon_id) as part of its CREATE TABLE statement.
- Constraints (per the `WLIST_DDL` string in `package_wlist.py`; exported to OUTPUT_DIR as wlist.ddl)
  - Unique: wlist_taxon_name_ukey on taxon_name; wlist_taxon_scientific_name_ukey on taxon_scientific_name.
  - Foreign key: wlist_aust_rli_fkey (aust_rli → lut_rli.id) ON UPDATE CASCADE ON DELETE SET NULL.
  - Checks: wlist_coastal_range_check (coastal_range IN (1, 2)); wlist_alist_change_check (alist_change IN (0, 0.5, 1)); wlist_ssp_ultrataxon_check (if taxon_level = 'ssp' then is_ultrataxon must be TRUE).
- Triggers
  - No triggers are included in the SQL dump. If the source database has triggers on these tables, they are not exported by this script.
- Other notes
  - For non-wlist tables (lut_rli and avilist_changes), the CREATE TABLE statements in the SQL dump are generated from pandas DataFrame dtypes at export time. As such, types are chosen generically (e.g., TEXT, DOUBLE PRECISION, BOOLEAN, BIGINT) and no keys/constraints are defined for these tables in the dump.

Tables and fields (metadata)

1) Core list (public.wlist -> wlist_core.csv / SQL table public.wlist)
- Source: SELECT of key columns from wlist plus a left-join to lut_rli to include aust_rli_status_desc.
- Ordering: taxon_sort asc.
- Primary key (SQL dump): taxon_id.

Fields (as table)

| Field                  | Type          | Description                                              |
|------------------------|---------------|----------------------------------------------------------|
| taxon_sort             | integer       | Sort order for taxa.                                     |
| is_ultrataxon          | smallint      | 1 if ultrataxon, 0 otherwise.                            |
| taxon_level            | varchar(50)   | Taxonomic level label.                                   |
| sp_id                  | smallint      | Species ID (legacy reference).                           |
| taxon_id               | varchar(20)   | Primary identifier for taxon (PK in SQL dump).           |
| taxon_name             | varchar(255)  | Common name.                                             |
| taxon_scientific_name  | varchar(255)  | Scientific name.                                         |
| family_name            | varchar(255)  | Family common name.                                      |
| family_scientific_name | varchar(255)  | Family scientific name.                                  |
| order                  | varchar(255)  | Taxonomic order (quoted identifier "order" in SQL).     |
| avibase_id             | varchar(255)  | External Avibase identifier.                             |
| bird_group             | varchar(255)  | Bird group/category.                                     |
| population             | varchar(255)  | Population/region qualifier.                             |
| coastal_range          | varchar(255)  | Coastal/inland descriptor.                               |
| aust_rli_1990          | smallint      | Red List Index (1990).                                   |
| aust_rli_2000          | smallint      | Red List Index (2000).                                   |
| aust_rli_2010          | smallint      | Red List Index (2010).                                   |
| aust_rli               | smallint      | Red List Index (current/overall code).                   |
| aust_rli_status_desc   | varchar(255)  | Description/label matched from lut_rli.category.         |

2) Red List Index lookup (lut_rli -> lut_rli.csv / SQL table lut_rli)
- Source: SELECT id, code, category FROM lut_rli.
- Notes on types: Exported SQL types are inferred from the data at runtime. Typical logical types are listed below; actual dump may use BIGINT/TEXT.

Fields (as table)

| Field    | Type    | Description                                         |
|----------|---------|-----------------------------------------------------|
| id       | integer | RLI category identifier (numeric key).              |
| code     | text    | Short code (e.g., two-letter code).                 |
| category | text    | Human-readable category/description.                |

3) Avilist changes (avilist_changes -> avilist_changes.csv / SQL table avilist_changes)
- Source: SELECT of taxon_id, a text label for alist_change (derived from numeric codes), and alist_change_note from wlist where alist_change is not null; ordered by taxon_sort.
- Note: The alist_change field in this export is a derived text label, not the original numeric value (1, 0.5, 0).
- Notes on types: Exported SQL types are inferred from the data at runtime. Typical logical types are listed below; actual dump may use TEXT for all three columns.

Fields (as table)

| Field            | Type        | Description                                                                  |
|------------------|-------------|------------------------------------------------------------------------------|
| taxon_id         | varchar(20) | Wlist primary key value.                                                     |
| alist_change     | text        | Derived label: 'Implementable' &#124; 'Not implementable' &#124; 'Partially implementable'. |
| alist_change_note| text        | Free-text note providing additional detail.                                  |

CSV formatting details
- Encoding: UTF-8.
- Quoting: Non-numeric values are quoted; numerics are left unquoted.
- Delimiter: comma.
- Header row is included.

SQL dump details
- File: wlist_core.sql
- Contents:
  - SET client_encoding = 'UTF8';
  - CREATE TABLE public.wlist (...) with a primary key on taxon_id.
  - CREATE TABLE statements for lut_rli and avilist_changes with generically inferred column types (no keys/constraints).
  - INSERT statements for all rows in each table (wlist, lut_rli, avilist_changes).
- Exclusions: No indexes (beyond the PK), no foreign keys, no triggers, no views/materialized views, no sequences.

Reproducibility and environment
- The export pulls live data at run time using the connection details above. If repeatability is required, capture the resulting CSV and SQL files in version control or an artifact store.
- Column types in the non-wlist CREATE TABLEs depend on the observed pandas dtypes; if you need exact SQL types, edit the script to provide an explicit DDL like the fixed WLIST_DDL used for public.wlist.

Changelog (editing aid)
- Please edit the field descriptions above to suit your domain language.
- If package_wlist.py is updated (queries, columns, or output directory), update this document accordingly.

| **FIELD**         | **TYPE**    | **DESCRIPTION**                                              |
| ----------------- | ----------- | ------------------------------------------------------------ |
| taxon_id          | varchar(20) | Wlist primary key value.                                     |
| alist_change      | text        | Derived label: 'Implementable' \| 'Not implementable' \| 'Partially  implementable'. |
| alist_change_note | text        | Free-text note providing additional detail.                  |



| **bird_group**                 | **description**                                              |
| ------------------------------ | ------------------------------------------------------------ |
| Terrestrial                    | Taxa with distributions characterised by irregular  occurrence patterns forming polygonal geometries with relatively low  edge-interior ratios and which depend on terrestrial habitats (as defined by  Garnett et al. 2015). |
| Wetland                        | Taxa with distributions characterised by irregular  occurrence patterns forming polygonal geometries with relatively low  edge-interior ratios and which depend on habitats of inland waters (as  defined by Garnett et al. 2015). |
| Shoreline (migratory/resident) | Taxa associated with linear habitats (shorelines of coasts  or inland waters) |
| Marine                         | Taxa with distributions characterised by irregular  occurrence (point) patterns forming polygonal geometries, and which feed  primarily in Marine habitats (as defined by Garnett et al. 2015). |



| **population**                 | **description**                                              |
| ------------------------------ | ------------------------------------------------------------ |
| Australian                     | Australian breeding population of taxa that also breed  elsewhere. |
| Endemic                        | Taxa which occur in Australia and nowhere else.              |
| Endemic (breeding only)        | Taxa which breed only in Australia, but which migrate  disperse frequently elsewhere. |
| Extinct (endemic)              | Taxa that occurred naturally only in Australia at the time  of European settlement (~1788) but are now extinct. |
| Extinct (Australia only)       | Taxa that occurred naturally in Australia at the time of  European settlement (~1788) but are now extinct in Australia, but which  persist elsewhere. |
| Failed introduction            | Taxa introduced to Australia for which wild populations  have not persisted (generally by acclimatisation societies early in European  settlement). |
| Introduced                     | taxon that has been introduced to Australia since 1788 and  established self-sustaining wild populations |
| Non-breeding                   | Occurs regularly in Australia but breeds elsewhere.          |
| Vagrant                        | Non-breeding taxa that cross into Australian  jurisdictional boundaries in insignificant numbers – i.e. <1% of the  estimated global population. |
| Vagrant (from NZ introduction) | Vagrants derived from populations successfully introduced  to New Zealand. |



| **is_coastal** | **description**                                        |
| -------------- | ------------------------------------------------------ |
| Obligate       | Strictly coastal, never found away from coasts.        |
| Facultative    | Principally coastal, but less frequently found inland. |



| **value** | CODE | **description (red list status)** |
| --------- | ---- | --------------------------------- |
| 0         | LC   | Least Concern                     |
| 1         | NT   | Near Threatened                   |
| 2         | VU   | Vulnerable                        |
| 3         | EN   | Endangered                        |
| 4         | CR   | Critically Endangered             |
| 5         | EX   | Extinct                           |
