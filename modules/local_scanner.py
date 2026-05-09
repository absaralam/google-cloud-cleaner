"""
local_scanner.py — Scan a local folder and index files by (name, extension).
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple


def scan_local_folder(folder_path: str, recursive: bool = True) -> Dict[Tuple[str, str], List[str]]:
    """
    Walk a local folder and build a dict keyed by (filename_lower, ext_lower).
    Value is a list of full file paths (there may be duplicates locally).

    Args:
        folder_path: Path to the local folder to scan.
        recursive:   If True, scan subdirectories too.

    Returns:
        {("photo", ".jpg"): ["C:\\Users\\...\\photo.jpg", ...], ...}
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Local folder not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder_path}")

    index: Dict[Tuple[str, str], List[str]] = {}

    walker = folder.rglob("*") if recursive else folder.glob("*")
    for entry in walker:
        if entry.is_file():
            stem = entry.stem.lower()
            ext  = entry.suffix.lower()
            key  = (stem, ext)
            index.setdefault(key, []).append(str(entry))

    return index


def summarize_local(index: Dict[Tuple[str, str], List[str]]) -> None:
    """Print a brief summary of the local scan results."""
    total_files  = sum(len(v) for v in index.values())
    unique_keys  = len(index)
    print(f"[LOCAL] Found {total_files} file(s) across {unique_keys} unique (name, ext) combinations.")
