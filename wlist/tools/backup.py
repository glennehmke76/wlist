"""
Backup utility for the wlist folder.

Creates/uses a sibling folder named "wlist_backup" (next to the wlist folder)
and writes each backup into a subfolder named by the current local date/time.

Also appends a log entry to an ASCII log file in the wlist folder
(wlist/backup.log) recording date/time, destination, and status.

Usage:
    python -m wlist.tools.backup

Optional args:
    --when <YYYYmmdd_%H%M%S>  Use explicit timestamp label instead of 'now'.
    --dry-run                 Show planned actions without copying.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
from pathlib import Path
from typing import Iterable


def _default_timestamp() -> str:
    # Using local time; format safe for file names
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _human_bytes(n: int) -> str:
    # Pretty-print bytes
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n //= 1024 if unit == "B" else n / 1024  # keep final TB as float
    return f"{n:.1f} TB"


def _iter_ignored_names() -> Iterable[str]:
    # Names to ignore when copying the wlist folder
    return {
        "__pycache__",
        ".pytest_cache",
        ".idea",
        ".DS_Store",
        ".ipynb_checkpoints",
        "wlist_backup",  # avoid recursion in case someone nests
    }


def _copytree(src: Path, dst: Path) -> tuple[int, int]:
    """Copy directory tree from src to dst with sane ignores.

    Returns (files_copied, bytes_copied).
    """
    ignore = shutil.ignore_patterns(*_iter_ignored_names())
    shutil.copytree(src, dst, ignore=ignore, dirs_exist_ok=False)

    files = 0
    size = 0
    for root, _dirs, fnames in os.walk(dst):
        for f in fnames:
            files += 1
            try:
                size += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return files, size


essential_paths = {
    # paths (relative to the domain repo root) that indicate we found the
    # right source folder (defensive) — updated for the wlist/wlist/{core,
    # ingest,build,tools} code-package layout (was a flat "package_wlist.py"
    # check when backup.py lived at the domain repo root)
    "README.md",
    os.path.join("wlist", "build", "package_wlist.py"),
}


def run_backup(when: str | None = None, dry_run: bool = False) -> Path:
    # backup.py now lives at wlist/wlist/tools/backup.py (three levels below
    # the domain repo root), so climb back up to it rather than assuming
    # __file__'s immediate parent is the folder to back up.
    wlist_dir = Path(__file__).resolve().parents[2]  # .../wlist (domain repo root)
    parent = wlist_dir.parent                        # .../py_proj
    backup_root = parent / "wlist_backup"
    ts = when or _default_timestamp()
    dest = backup_root / ts

    # Minimal sanity check: ensure we're backing up the intended folder
    if not all((wlist_dir / name).exists() for name in essential_paths):
        raise RuntimeError(f"Unexpected source folder, missing required files in {wlist_dir}")

    # Prepare messages
    msg_hdr = f"[wlist.backup] {ts}"

    if dry_run:
        print(f"{msg_hdr} DRY-RUN: would copy '{wlist_dir.name}' -> '{dest}'")
        return dest

    backup_root.mkdir(parents=True, exist_ok=True)

    # Perform copy
    files_copied = 0
    bytes_copied = 0
    status = "OK"
    err_text = ""
    try:
        files_copied, bytes_copied = _copytree(wlist_dir, dest)
    except Exception as e:  # noqa: BLE001 — log and re-raise after logging
        status = "ERROR"
        err_text = f"{e.__class__.__name__}: {e}"
    finally:
        # Always attempt to log
        _append_log(
            wlist_dir / "backup.log",
            ts=ts,
            dest=str(dest),
            status=status,
            files=files_copied,
            bytes=bytes_copied,
            error=err_text,
        )

    if status != "OK":
        # Clean up a partial destination if it exists (best effort)
        try:
            if dest.exists():
                shutil.rmtree(dest)
        except Exception:
            pass
        raise RuntimeError(f"Backup failed: {err_text}")

    print(
        f"{msg_hdr} Backup completed: {files_copied} files, {_human_bytes(bytes_copied)} -> {dest}"
    )
    return dest


def _append_log(log_path: Path, *, ts: str, dest: str, status: str, files: int, bytes: int, error: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not log_path.exists()
    line = (
        f"{ts}\tstatus={status}\tdest={dest}\tfiles={files}\tsize_bytes={bytes}"
        + (f"\terror={error}" if error else "")
        + "\n"
    )
    with log_path.open("a", encoding="utf-8") as f:
        if header_needed:
            f.write("# wlist backup log\n")
            f.write("# ts\tstatus\tdest\tfiles\tsize_bytes\terror\n")
        f.write(line)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backup the wlist folder to wlist_backup/<timestamp>.")
    p.add_argument("--when", default=None, help="Timestamp label to use (YYYYmmdd_HHMMSS). Defaults to now().")
    p.add_argument("--dry-run", action="store_true", help="Show actions without copying.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    run_backup(when=args.when, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
