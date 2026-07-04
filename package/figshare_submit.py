"""
figshare_submit.py
==================
Submit the 'A Working List of Australian Birds' data package to figshare.

Usage
-----
1. Create a personal access token at https://figshare.com/account/applications
2. Set the token in the environment (preferred):
       export FIGSHARE_TOKEN="your_token_here"
   OR paste it into the FIGSHARE_TOKEN constant below (remove before sharing).
3. Run:
       python figshare_submit.py

Modes
-----
  python figshare_submit.py              # dry run — prints metadata only, no API calls
  python figshare_submit.py --create     # creates item and uploads files (does NOT publish)
  python figshare_submit.py --publish    # publishes the item (makes it public with a DOI)
                                         # Only run --publish after reviewing the item in
                                         # the figshare web interface.

Requirements
------------
  pip install requests

Notes
-----
- figshare API base: https://api.figshare.com/v2
- Rate limits: 10 requests/second; no bulk upload limit documented.
- Large files (>20 MB): the script uses the multipart upload endpoint automatically.
- Once published, a DOI is minted and the item is publicly visible. You cannot
  un-publish without contacting figshare support.
- For institutional portal submissions, set GROUP_ID to your institution's group integer.
  Leave as None for a personal account item.
"""

import os
import sys
import json
import hashlib
import math
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed — run: pip install requests")

# =============================================================================
# CONFIGURATION — edit these before running
# =============================================================================

FIGSHARE_TOKEN = os.environ.get("FIGSHARE_TOKEN", "")  # Set via env var; see Usage above

BASE_URL = "https://api.figshare.com/v2"
PACKAGE_DIR = Path(__file__).parent  # Directory containing this script

# Institution group ID — set to your institution's integer group ID if submitting
# to an institutional portal (e.g. CDU figshare). Leave as None for personal account.
GROUP_ID = None  # e.g. 12345

# Files to upload (relative to PACKAGE_DIR).
# Order matters — README first, main data second.
FILES = [
    "README.md",
    "A working list of Australian birds.pdf",
    "wlist_core.csv",
    "wlist_core_data_dictionary.csv",
    "avilist_changes.csv",
    "wlist_avilist_changes.pdf",
    "lut_rli.csv",
    "wlist_lut_rli_data_dictionary.csv",
    "wlist.ddl",
    "wlist_core.sql",
    "wlist_dqa_report.md",
]

# figshare category IDs (integers). Verify/update via:
#   GET https://api.figshare.com/v2/categories  (no auth required)
# Verified IDs from GET https://api.figshare.com/v2/categories (2026-05-28):
#   26881 = Ecological applications
#   26932 = Conservation and biodiversity
#   24244 = Animal systematics and taxonomy  (Ornithology not available as category)
#   24235 = Terrestrial ecology
CATEGORY_IDS = [26932, 24244, 24235]

# License ID. 1 = CC BY 4.0
# Full list: GET https://api.figshare.com/v2/licenses
LICENSE_ID = 1

# =============================================================================
# METADATA
# =============================================================================

ITEM_METADATA = {
    "title": "A Working List of Australian Birds",

    "authors": [
        {"id": 23241993},                  # Ehmke, Glenn — existing figshare account
        {"name": "O'Connor, James"},       # ORCID TBC
        # {"name": "Garnett, Stephen", "orcid_id": "0000-0002-0724-7060"},
    ],

    # description: plain text or HTML. Combines abstract, purpose, spatial context,
    # methods summary, and DQA note as recommended in figshare_conversion_strategy.md.
    "description": (
        "<p>This dataset is a structured inventory of Australian birds, including all species "
        "and subspecies (ultrataxa) with ecological or conservation relevance within Australian "
        "jurisdictions. For each taxon, the dataset provides stable unique identifiers, scientific "
        "and common names, higher-order taxonomic classifications, spatial bird group and population "
        "descriptors, coastal range classification, an external Avibase identifier, and Australian "
        "Red List Index (RLI) extinction risk values across four assessment periods (1990, 2000, "
        "2010, and current). The dataset comprises 1,739 taxon rows.</p>"

        "<p><strong>Purpose</strong><br>"
        "The primary purpose of this list is to maintain a stable and consistent taxonomic framework "
        "for organising biodiversity data while accommodating ongoing changes in taxonomy. Taxonomy "
        "is treated as an evolving scientific framework, whereas ecological observations and "
        "conservation data must remain interpretable through time. The list uses stable, unique "
        "identifiers for all taxa, records taxa at the finest practical resolution (ultrataxa), "
        "and aligns with global taxonomies with transparent, limited deviations. This supports "
        "long-term data usability, reproducibility of analyses, and integration across spatial range "
        "layers, ecological trait databases, conservation assessments, and bird occurrence records.</p>"

        "<p><strong>Methods</strong><br>"
        "The dataset was compiled through systematic synthesis of published global and regional "
        "taxonomies, authoritative subspecies inventories, and successive Australian bird conservation "
        "assessments. Species-level classifications follow AviList (AviList Core Team 2025). "
        "Subspecies listings draw on Schodde and Mason (1997, 1999), the Handbook of Australian, "
        "New Zealand and Antarctic Birds, and published taxonomic works. Extinction risk assessments "
        "were sourced from successive Action Plans for Australian Birds, with interim updates applied. "
        "All taxa are assigned stable unique identifiers; AviList v1 integration changes are "
        "documented in avilist_changes.csv.</p>"

        "<p><strong>Spatial coverage</strong><br>"
        "Total Australian Territory. Bounding box: N &minus;9.1333, E 167.95, S &minus;54.85, "
        "W 72.5667 (WGS 84 / EPSG:4326).</p>"

        "<p><strong>Data quality</strong><br>"
        "Data quality was assessed using a custom Python function against the operational PostgreSQL "
        "database. All primary integrity checks pass (0 referential integrity violations, 0 constraint "
        "violations, 0 duplicate identifiers or names). AviBase ID coverage: 98.2%; Australian RLI "
        "coverage: 72.2% (484 taxa without formal assessment, as expected). "
        "Full report: see wlist_dqa_report.md in package files.</p>"

        "<p><strong>Versioning</strong><br>"
        "Version 1. Dataset created 01/12/2025. Maintenance frequency: annual.</p>"
    ),

    "categories": CATEGORY_IDS,

    "tags": [
        "Australian birds",
        "avifauna",
        "working list",
        "taxonomy",
        "nomenclature",
        "subspecies",
        "ultrataxa",
        "conservation",
        "Red List Index",
        "AviList",
        "Avibase",
        "ornithology",
        "Australia",
        "biodiversity",
        "ecological assessment",
        "taxon identifiers",
    ],

    "license": LICENSE_ID,

    # defined_type: "dataset" | "figure" | "media" | "poster" | "paper" |
    #               "presentation" | "thesis" | "code" | "online resource" |
    #               "preprint" | "software" | "collection" | "book"
    "defined_type": "dataset",

    # funding: free-text or structured. Update with actual grant details.
    # "funding": "Charles Darwin University HDR Scholarship; [grant name if applicable]",

    # references: related publications, source records, etc. Update with actual DOIs.
    # "references": [
    #     "https://doi.org/10.1071/9780643107403",  # Garnett and Baker 2021
    # ],

    # resource_doi / resource_title: if the data paper has been published, add its DOI here.
    # "resource_doi": "https://doi.org/10.xxxx/xxxxx",
    # "resource_title": "A Working List of Australian Birds",
}

# Add group_id if submitting to an institutional portal
if GROUP_ID is not None:
    ITEM_METADATA["group_id"] = GROUP_ID

# =============================================================================
# HELPERS
# =============================================================================

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks for multipart upload


def headers():
    if not FIGSHARE_TOKEN:
        sys.exit(
            "\nNo figshare token found.\n"
            "Set the FIGSHARE_TOKEN environment variable:\n"
            "    export FIGSHARE_TOKEN='your_token_here'\n"
        )
    return {"Authorization": f"token {FIGSHARE_TOKEN}"}


def api(method, endpoint, **kwargs):
    """Make a figshare API call; raise on error."""
    url = f"{BASE_URL}{endpoint}"
    resp = getattr(requests, method)(url, headers=headers(), **kwargs)
    if not resp.ok:
        sys.exit(
            f"\nAPI error {resp.status_code} on {method.upper()} {endpoint}:\n"
            f"{resp.text}\n"
        )
    return resp.json() if resp.content else {}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_file(item_id: int, file_path: Path):
    """Upload a single file using figshare's multipart upload protocol."""
    size = file_path.stat().st_size
    parts = math.ceil(size / CHUNK_SIZE) or 1

    print(f"  Uploading {file_path.name} ({size / 1024 / 1024:.1f} MB) …", end="", flush=True)

    # 1. Initiate upload
    file_info = api(
        "post",
        f"/account/articles/{item_id}/files",
        json={"name": file_path.name, "size": size, "md5": md5(file_path)},
    )
    file_id = file_info["location"].split("/")[-1]

    # 2. Get upload URL and parts
    upload = api("get", f"/account/articles/{item_id}/files/{file_id}")
    upload_url = upload["upload_url"]
    upload_token = upload_url.split("upload_token=")[-1]

    # Upload service uses token-in-URL auth — do NOT send Authorization header
    upload_info = requests.get(upload_url).json()
    actual_parts = upload_info.get("parts", [{"startOffset": 0, "endOffset": size - 1, "partNo": 1}])

    # 3. Upload each part
    with open(file_path, "rb") as f:
        for part in actual_parts:
            start = part["startOffset"]
            end = part["endOffset"] + 1
            f.seek(start)
            chunk = f.read(end - start)
            part_url = f"{upload_url}/{part['partNo']}"
            resp = requests.put(part_url, data=chunk)  # no auth header — upload service uses URL token
            if not resp.ok:
                sys.exit(f"\nFailed to upload part {part['partNo']} of {file_path.name}: {resp.text}")
        print(".", end="", flush=True)

    # 4. Complete upload
    api("post", f"/account/articles/{item_id}/files/{file_id}/complete")
    print(" done")
    return file_id


# =============================================================================
# MAIN
# =============================================================================

def dry_run():
    print("\n=== DRY RUN — no API calls will be made ===\n")
    print("Metadata to be submitted:")
    print(json.dumps(
        {k: v for k, v in ITEM_METADATA.items() if k != "description"},
        indent=2,
    ))
    print(f"\ndescription: {ITEM_METADATA['description'][:200]}…")
    print(f"\nFiles to upload ({len(FILES)}):")
    total = 0
    for f in FILES:
        p = PACKAGE_DIR / f
        if p.exists():
            size = p.stat().st_size
            total += size
            print(f"  ✅  {f}  ({size / 1024:.0f} KB)")
        else:
            print(f"  ❌  {f}  — NOT FOUND at {p}")
    print(f"\nTotal upload size: {total / 1024 / 1024:.1f} MB")
    print("\nRun with --create to create the item and upload files.")
    print("Run with --publish to publish (only after reviewing in figshare web UI).")


def create_and_upload():
    print("\n=== Creating figshare item ===")
    result = api("post", "/account/articles", json=ITEM_METADATA)
    item_id = int(result["location"].split("/")[-1])
    print(f"Item created: ID {item_id}")
    print(f"Review at: https://figshare.com/account/articles/{item_id}\n")

    print("Uploading files:")
    for filename in FILES:
        path = PACKAGE_DIR / filename
        if not path.exists():
            print(f"  ⚠️  SKIPPED: {filename} not found at {path}")
            continue
        upload_file(item_id, path)

    print(f"\n✅  Upload complete. Item ID: {item_id}")
    print(f"Review and edit at: https://figshare.com/account/articles/{item_id}")
    print("\nWhen ready to publish, run:")
    print(f"    python {Path(__file__).name} --publish --item-id {item_id}")
    return item_id


def publish(item_id: int):
    print(f"\n=== Publishing item {item_id} ===")
    confirm = input(
        "⚠️  This will make the item publicly visible and mint a DOI.\n"
        "    Type 'yes' to confirm: "
    )
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return
    api("post", f"/account/articles/{item_id}/publish")
    item = api("get", f"/account/articles/{item_id}")
    doi = item.get("doi", "(DOI not yet available — check figshare web interface)")
    print(f"\n✅  Published. DOI: {doi}")
    print(f"URL: {item.get('figshare_url', 'https://figshare.com')}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--publish" in args:
        if "--item-id" in args:
            idx = args.index("--item-id")
            item_id = int(args[idx + 1])
        else:
            item_id_str = input("Enter item ID to publish: ").strip()
            item_id = int(item_id_str)
        publish(item_id)

    elif "--create" in args:
        create_and_upload()

    else:
        dry_run()
