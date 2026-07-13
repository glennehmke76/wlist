#!/usr/bin/env python3
"""
figshare_create_draft.py
========================
Convenience wrapper to create a private Figshare draft and upload files
without publishing. This simply forwards to create_and_upload() defined in
wlist/data_package/figshare/figshare_submit.py, while letting you pass a token on the CLI.

Usage
-----
- Preferred: set env var and run the underlying script directly:
    export FIGSHARE_TOKEN="<your_token>"
    python wlist/data_package/figshare/figshare_submit.py --create

- Or use this wrapper to pass the token inline:
    python wlist/data_package/figshare/figshare_create_draft.py --token <your_token>

Notes
-----
- This script never publishes; it only creates the draft and uploads files.
- Keep your token private. Do not commit it to source control.
- Review the created draft in the Figshare web UI and publish there, or run
  the underlying script with --publish when ready.
"""

from __future__ import annotations

import argparse
import os
import runpy
from pathlib import Path
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a private Figshare draft item and upload files (does NOT publish).",
        epilog=(
            "This is a thin wrapper around wlist/data_package/figshare/figshare_submit.py. "
            "You can run that script directly with --create as well."
        ),
    )
    parser.add_argument(
        "--token",
        help=(
            "Figshare personal access token. If omitted, the FIGSHARE_TOKEN "
            "environment variable must be set."
        ),
    )
    args = parser.parse_args(argv)

    if args.token:
        # Set only for current process and any child requests
        os.environ["FIGSHARE_TOKEN"] = args.token

    submit_path = Path(__file__).with_name("figshare_submit.py")
    if not submit_path.exists():
        print(f"Error: expected script not found at {submit_path}", file=sys.stderr)
        return 2

    # Load the submit script as a module-like namespace
    ns = runpy.run_path(str(submit_path))

    # Call create_and_upload from the loaded namespace
    try:
        item_id = ns["create_and_upload"]()
    except SystemExit as e:
        # Pass through exit code but add a friendlier hint for missing token
        msg = str(e)
        if "No figshare token" in msg or "FIGSHARE_TOKEN" in msg:
            print(
                "Missing token. Provide --token <TOKEN> or set FIGSHARE_TOKEN in the environment.",
                file=sys.stderr,
            )
            return 3
        raise

    # Print a succinct success message
    print(f"\nDraft created (not published). Item ID: {item_id}")
    print(f"Review at: https://figshare.com/account/articles/{item_id}")
    print("\nNext steps: Review in the Figshare web UI and publish when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
