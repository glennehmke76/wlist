# add_taxon — add one or more rows to wlist via the stored procedure wlist_add_row

## Overview
- Calls the PostgreSQL procedure `wlist_add_row` to insert a new taxon just below a target `taxon_sort` and shifts following rows to keep ordering contiguous.
- Uses your existing psycopg2 connector from `package_wlist.get_db_connection()`.
- Supports CSV or JSON input, friendly CSV headers, pre-checks, all‑or‑nothing transactions, and a dry‑run mode that validates and surfaces server NOTICEs without committing.

## Quick start (CLI)
- Dry‑run from CSV (recommended first):
  ```bash
  python -m wlist.add_taxon.add_taxon --csv wlist/add_taxon/sample_add_taxon.csv --dry-run
  # (Alternative if running as a plain script)
  python wlist/add_taxon/add_taxon.py --csv wlist/add_taxon/sample_add_taxon.csv --dry-run
  ```
- Commit from CSV:
  ```bash
  python -m wlist.add_taxon.add_taxon --csv /path/to/your_rows.csv
  # or
  python wlist/add_taxon/add_taxon.py --csv /path/to/your_rows.csv
  ```
- Dry‑run/commit from JSON:
  ```bash
  # Using the provided sample JSON
  python -m wlist.add_taxon.add_taxon --json wlist/add_taxon/sample_add_taxon.json --dry-run
  
  # Your own JSON file
  python -m wlist.add_taxon.add_taxon --json /path/to/your_rows.json
  # or
  python wlist/add_taxon/add_taxon.py --json /path/to/your_rows.json
  ```

## Arguments
- `--csv PATH`: Path to a CSV file whose headers match either friendly names or the exact procedure parameter names (see Headers below).
- `--json PATH`: Path to a JSON file containing one object or an array of objects. Keys can be friendly names or exact procedure parameter names.
- `--dry-run`: Execute and show server NOTICEs, then roll back the transaction. No changes are persisted.

## Environment variables (used by package_wlist.get_db_connection)
- `DCORE_HOST` (default: localhost)
- `DCORE_DB` (default: dcoredb)
- `DCORE_USER` (default: glennehmke)
- `DCORE_PASSWORD` (no default — set via env var or `~/.pgpass`)
- `DCORE_PORT` (default: 5432)

## CSV/JSON headers
- You may use either of the following styles for keys/headers:
  - Friendly headers (mapped automatically):
    ```text
    taxon_sort_target, is_ultrataxon, taxon_level, sp_id, taxon_id, taxon_name, taxon_scientific_name, family_name, family_scientific_name, order (or t_order), population, aust_rli_1990, aust_rli_2000, aust_rli_2010, aust_rli, bird_group, supplementary, avibase_id, reference
    ```
  - Exact stored-proc parameter names (positional order is handled internally):
    ```text
    p_taxon_sort_target, p_taxon_id, p_is_ultrataxon, p_taxon_level, p_sp_id, p_taxon_name, p_taxon_scientific_name, p_family_name, p_family_scientific_name, p_t_order, p_population, p_aust_rli_1990, p_aust_rli_2000, p_aust_rli_2010, p_aust_rli, p_bird_group, p_supplementary, p_avibase_id, p_reference
    ```
- Missing fields are treated as NULL.
- Integer-like fields are validated and cast: `p_taxon_sort_target`, `p_is_ultrataxon`, `p_sp_id`, `p_aust_rli_1990`, `p_aust_rli_2000`, `p_aust_rli_2010`, `p_aust_rli`, `p_supplementary`.

## CSV format, encoding, and quoting
- Encoding: UTF-8 without BOM (byte-order mark). Some tools (e.g., Excel "CSV UTF-8") may insert a BOM which can make the first header not match; prefer saving as standard CSV (comma delimited) or ensure no BOM is present. If you must work with a BOM, remove it before loading.
- Delimiter: Comma (,).
- Quoting: Double quotes (") are used for fields that contain commas, double quotes, or newlines. To include a literal double quote inside a field, double it (e.g., She said ""hi"").
- Newlines in fields: Supported when the field is quoted.
- Line endings: LF or CRLF are both fine.
- Header row: Required as the first row; headers must exactly match the friendly names or the exact p_* parameter names listed above (case/space insensitive mapping is applied, but avoid invisible characters).
- Whitespace: Leading/trailing spaces in cell values are trimmed; empty cells are treated as NULL.
- Numbers: Provide plain digits only (no thousands separators or units). Integer-like fields listed above are validated and cast to integers.
- Tips for Excel/Sheets:
  - Prefer plain ASCII quotes and commas; avoid “smart quotes”.
  - If your tool insists on adding a BOM, you can paste the data into a UTF-8 (no BOM) editor and resave, or export via Google Sheets which typically omits the BOM.

## Validation and behavior
- Required: `p_taxon_sort_target`, `p_is_ultrataxon` (0 or 1).
- If `p_is_ultrataxon != 1`, then `p_taxon_id` must be provided.
- `p_taxon_sort_target` must already exist in `wlist` (safety check to avoid large shifts).
- If `p_taxon_id` is provided, it must not already exist in `wlist` (duplicate check).
- If `p_sp_id` is not provided, the procedure auto-assigns the next available in 5001–7999.
- If `p_taxon_id` is not provided for ultrataxons, the procedure generates `'u' || sp_id`.

## Examples
- CSV examples
  - Minimal ultrataxon (auto sp_id and taxon_id):
    ```csv
    taxon_sort_target,is_ultrataxon,taxon_level,sp_id,taxon_id,taxon_name,taxon_scientific_name,family_name,family_scientific_name,order,population,aust_rli_1990,aust_rli_2000,aust_rli_2010,aust_rli,bird_group,supplementary,avibase_id,reference
    1729,1,ssp,,,,"Common Redpoll (ssp)","Acanthis flammea cabaret","Old World Finches","Fringillidae","Passeriformes","Introduced",,,,,,,
    ```
  - Full field specification (non‑ultrataxon):
    ```csv
    taxon_sort_target,is_ultrataxon,taxon_level,sp_id,taxon_id,taxon_name,taxon_scientific_name,family_name,family_scientific_name,order,population,aust_rli_1990,aust_rli_2000,aust_rli_2010,aust_rli,bird_group,supplementary,avibase_id,reference
    2000,0,species,5123,u5123,Some Bird,Genus species,Family,FamilySci,Order,Native,1990,2000,2010,2020,Subgroup,0,ABCD-1234,Ref text
    ```
  - Notes:
    - You may also use exact proc param headers instead of friendly ones:
      ```csv
      p_taxon_sort_target,p_taxon_id,p_is_ultrataxon,p_taxon_level,p_sp_id,p_taxon_name,p_taxon_scientific_name,p_family_name,p_family_scientific_name,p_t_order,p_population,p_aust_rli_1990,p_aust_rli_2000,p_aust_rli_2010,p_aust_rli,p_bird_group,p_supplementary,p_avibase_id,p_reference
      2000,u5123,0,species,5123,Some Bird,Genus species,Family,FamilySci,Order,Native,1990,2000,2010,2020,Subgroup,0,ABCD-1234,Ref text
      ```
    - Legacy header alias supported: bird_sub_group will be accepted and mapped to bird_group.

- JSON examples
  - Minimal ultrataxon (auto sp_id and taxon_id):
    ```json
    [
      {
        "taxon_sort_target": 1729,
        "is_ultrataxon": 1,
        "taxon_level": "ssp",
        "taxon_name": "Common Redpoll (ssp)",
        "taxon_scientific_name": "Acanthis flammea cabaret",
        "family_name": "Old World Finches",
        "family_scientific_name": "Fringillidae",
        "order": "Passeriformes",
        "population": "Introduced"
      }
    ]
    ```
  - Full field specification (non‑ultrataxon):
    ```json
    [
      {
        "taxon_sort_target": 2000,
        "is_ultrataxon": 0,
        "taxon_level": "species",
        "sp_id": 5123,
        "taxon_id": "u5123",
        "taxon_name": "Some Bird",
        "taxon_scientific_name": "Genus species",
        "family_name": "Family",
        "family_scientific_name": "FamilySci",
        "order": "Order",
        "population": "Native",
        "aust_rli_1990": 1990,
        "aust_rli_2000": 2000,
        "aust_rli_2010": 2010,
        "aust_rli": 2020,
        "bird_group": "Subgroup",
        "supplementary": 0,
        "avibase_id": "ABCD-1234",
        "reference": "Ref text"
      }
    ]
    ```

## Python usage (API)
- You can import and use the functions directly:
  ```python
  from wlist.add_taxon.add_taxon import add_wlist_rows_psycopg2, load_rows_from_csv
  
  # From CSV
  rows = list(load_rows_from_csv("wlist/add_taxon/sample_add_taxon.csv"))
  result = add_wlist_rows_psycopg2(rows, dry_run=True)
  print(result)
  
  # From JSON file
  import json
  from wlist.add_taxon.add_taxon import add_wlist_rows_psycopg2
  
  with open("wlist/add_taxon/sample_add_taxon.json", "r", encoding="utf-8") as f:
      rows = json.load(f)
  result = add_wlist_rows_psycopg2(rows, dry_run=True)
  print(result)
  
  # From in-memory dictionaries
  rows = [
      {
          "taxon_sort_target": 1729,
          "is_ultrataxon": 1,
          "taxon_level": "ssp",
          "taxon_name": "Common Redpoll (ssp)",
          "taxon_scientific_name": "Acanthis flammea cabaret",
          "family_name": "Old World Finches",
          "family_scientific_name": "Fringillidae",
          "order": "Passeriformes",
          "population": "Introduced",
      }
  ]
  result = add_wlist_rows_psycopg2(rows, dry_run=False)
  print(result)
  ```

## Should we include a default CSV in this folder?
- Yes, a template CSV is provided as `sample_add_taxon.csv` to make authoring rows easy (works with Excel/Sheets). It is safe by default and intended for dry‑run testing.
- Recommendation: Do not hard‑code this file as the default input path in the CLI to avoid accidental production inserts. Always require callers to pass `--csv/--json` explicitly. Use `--dry-run` first when editing the template.

## Troubleshooting
- psycopg2/connection errors: ensure `DCORE_*` environment variables are set correctly and the DB is reachable.
- Procedure errors (e.g., missing `p_taxon_id` when `p_is_ultrataxon=0`): run with `--dry-run` to see the server NOTICEs and error messages without committing.
- Header issues: verify your CSV headers are either friendly or exact proc parameter names listed above.
- Hint: If you previously saw an error like "procedure wlist_add_row(...) does not exist" when many NULLs were passed, the tool now uses named arguments with explicit type casts in the CALL to avoid PostgreSQL's unknown-type ambiguity. Ensure your database has the current procedure signature (bird_group, not bird_sub_group).

## License/Notes
- This tool modifies ordering in `wlist` by design (it shifts `taxon_sort` values). Prefer running during a quiet window to avoid conflicting edits.
