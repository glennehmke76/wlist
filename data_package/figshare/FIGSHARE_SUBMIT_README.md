Figshare submission workflow (read this before running figshare_submit.py)

Where to actually run this from (updated 2026-07-13, ADR-005/007 — collapses the
former ADR-003 two-location split)
- `figshare_submit.py` here is the canonical, version-controlled source — edit it here.
- It looks for its FILES list (the packaged CSVs/PDF/SQL/DQA report) in
  `data_package/build/` (`PACKAGE_DIR = Path(__file__).parent.parent / "build"`), which
  is now inside this git repo — `package_wlist.py`'s `OUTPUT_DIR` writes there directly.
- No more syncing a second copy to `Taxonomy/wlist/package/` — run it straight from
  `data_package/figshare/` in this repo.
- See wlist strategy `strategy/02_wlist_dev_log.md` ADR-003 (original split) and ADR-007
  (this session's consolidation) for the full reasoning.

Summary
- Yes — by design. The --create mode only creates the item and uploads the files; it does not publish. Figshare holds it as a private draft in your account, invisible to anyone else, with no DOI minted yet.
- Publishing is a separate, explicit step gated by a flag and a confirmation prompt. You can also publish from the web UI if you prefer.

Prerequisites
- Create a Personal Access Token in Figshare: https://figshare.com/account/applications
- Set the token in your environment (recommended):
  export FIGSHARE_TOKEN="your_token_here"
- Requires: pip install requests

Where the script lives
- Script path: wlist/data_package/figshare/figshare_submit.py
- Run commands from that directory or provide the path to the script when invoking Python.

The flow
1) Dry run — no API calls; validates files and prints metadata
   python figshare_submit.py
   What it does:
   - Prints the metadata that would be sent (title, authors, categories, tags, etc.)
   - Lists all files it expects to upload and whether they are present, with sizes
   - Does not contact the Figshare API

2) Create draft and upload files — does NOT publish
   python figshare_submit.py --create
   What it does:
   - Creates a private draft item in your Figshare account (or group if configured)
   - Uploads the package files (uses multipart upload for large files automatically)
   - Prints the numeric item ID and a direct link to the draft in your account
   Note:
   - At this stage the item is private. No DOI is minted. Only you (and your group, if applicable) can see it.

3) Review in the Figshare web UI
   - Open the printed link (or navigate to your account → My data → the new draft)
   - Check/adjust: title, description, categories, tags, authors, funding, references
   - Reorder files, remove/add files if needed, and check file previews
   - When satisfied, you may either publish in the web UI directly, or proceed to step 4 to publish via the script

4) Publish — irreversible and mints the DOI
   Option A: Publish via the script (requires the item ID shown in step 2)
     python figshare_submit.py --publish --item-id <id>
     The script will prompt:
       Type 'yes' to confirm
     Only if you type yes will it publish the item and mint the DOI.

   Option B: Publish in the Figshare web UI
     - Open the draft item and click Publish

Important notes
- Publishing is the only irreversible step. Once published, a DOI is minted and the item is publicly visible. Unpublishing requires contacting Figshare support.
- You can safely run the dry run repeatedly. The --create step can also be repeated to create a new draft if you prefer to start over; just note that it will make another item (it does not overwrite the previous one).
- The script supports institutional submissions via GROUP_ID in the script configuration. If GROUP_ID is set, the draft is created under that group.
- Large files: The uploader switches to multipart uploads automatically using 10 MB chunks.

Troubleshooting
- Missing token: The script exits with instructions if FIGSHARE_TOKEN is not set.
- API errors: The script prints the HTTP code and Figshare error text and then exits.
- File not found: In dry run or create mode, the script reports any missing files it expects in data_package/build/. Add/rename files as needed and re-run.

Quick reference
- Dry run:    python figshare_submit.py
- Create:     python figshare_submit.py --create
- Publish:    python figshare_submit.py --publish --item-id <id>

This README reflects the logic implemented in figshare_submit.py and is intended to make the intended workflow explicit and safe.


CLI examples (copy-paste)

```bash
# 0) Ensure token is set in your shell first
export FIGSHARE_TOKEN="your_token_here"

# 1) Dry run — no API calls
python figshare_submit.py

# 2) Create draft + upload files (does NOT publish)
python figshare_submit.py --create

# 3) Publish the reviewed draft (irreversible; mints DOI)
python figshare_submit.py --publish --item-id <ITEM_ID>
```

Python usage example

```python
# Programmatic usage without installing as a package, using runpy to load the script.
# This assumes you run from the repo root so the relative path exists.

import os
import runpy

# 0) Ensure the token is set for API calls
os.environ["FIGSHARE_TOKEN"] = "your_token_here"

# 1) Load the script as a module namespace
ns = runpy.run_path("wlist/data_package/figshare/figshare_submit.py")

# 2) Inspect metadata and files locally (no API calls)
ns["dry_run"]()

# 3) Create a private draft and upload all files
item_id = ns["create_and_upload"]()
print(f"Draft created with ID: {item_id}")

# 4) Publish after manual review in the web UI (will prompt for 'yes')
ns["publish"](item_id)
```
