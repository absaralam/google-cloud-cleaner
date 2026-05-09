"""
drive_handler.py — Google Drive file listing and deletion.
Compares Drive files against a local index and optionally deletes matches.
"""

import sys
from typing import Dict, List, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Fields to fetch per Drive file
DRIVE_FIELDS = "nextPageToken, files(id, name, mimeType, size, trashed)"


def build_drive_service(creds):
    """Build and return a Google Drive API service object."""
    return build("drive", "v3", credentials=creds)


def list_drive_files(service, include_trashed: bool = False) -> List[Dict]:
    """
    Fetch all non-folder files from Google Drive (handles pagination).

    Returns:
        List of file dicts: {id, name, mimeType, size, trashed}
    """
    files = []
    page_token = None
    query = "mimeType != 'application/vnd.google-apps.folder'"
    if not include_trashed:
        query += " and trashed = false"

    print("[DRIVE] Fetching file list from Google Drive...", flush=True)
    while True:
        try:
            response = service.files().list(
                q=query,
                spaces="drive",
                fields=DRIVE_FIELDS,
                pageSize=1000,
                pageToken=page_token,
            ).execute()
        except HttpError as e:
            print(f"[DRIVE] API error while listing files: {e}")
            sys.exit(1)

        batch = response.get("files", [])
        files.extend(batch)
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"[DRIVE] Total files found in Drive: {len(files)}")
    return files


def find_drive_matches(
    drive_files: List[Dict],
    local_index: Dict[Tuple[str, str], List[str]],
) -> List[Dict]:
    """
    Find Drive files whose (stem, ext) match a key in local_index.

    Returns:
        List of matching Drive file dicts, each augmented with '_local_paths'.
    """
    from pathlib import PurePosixPath

    matches = []
    for f in drive_files:
        name = f.get("name", "")
        # Split into stem + ext using Python's pathlib
        p    = PurePosixPath(name)
        stem = p.stem.lower()
        ext  = p.suffix.lower()
        key  = (stem, ext)

        if key in local_index:
            f["_local_paths"] = local_index[key]
            f["_match_key"]   = key
            matches.append(f)

    return matches


def print_drive_matches(matches: List[Dict]) -> None:
    """Pretty-print matched Drive files."""
    if not matches:
        print("[DRIVE] No matching files found between Drive and local folder.")
        return

    print(f"\n[DRIVE] {len(matches)} file(s) in Google Drive match local files:\n")
    print(f"  {'#':<5} {'Drive File Name':<45} {'Drive ID':<35} {'Local Match'}")
    print(f"  {'-'*5} {'-'*45} {'-'*35} {'-'*40}")
    for i, f in enumerate(matches, 1):
        local_display = f["_local_paths"][0] if f["_local_paths"] else "?"
        print(f"  {i:<5} {f['name']:<45} {f['id']:<35} {local_display}")
    print()


def delete_drive_files(service, matches: List[Dict], dry_run: bool = True) -> None:
    """
    Delete matched Drive files.

    Args:
        service:  Drive API service.
        matches:  List of matched Drive file dicts.
        dry_run:  If True, only simulate (no actual deletion).
    """
    if not matches:
        print("[DRIVE] Nothing to delete.")
        return

    if dry_run:
        print(f"[DRIVE][DRY RUN] Would delete {len(matches)} file(s) from Google Drive.")
        print("[DRIVE][DRY RUN] Re-run with --execute to perform actual deletion.\n")
        return

    print(f"[DRIVE] Deleting {len(matches)} file(s) from Google Drive...")
    success = 0
    failed  = 0
    for f in matches:
        try:
            service.files().delete(fileId=f["id"]).execute()
            print(f"  [DELETED] {f['name']} ({f['id']})")
            success += 1
        except HttpError as e:
            print(f"  [FAILED]  {f['name']} ({f['id']}) — {e}")
            failed += 1

    print(f"\n[DRIVE] Done. Deleted: {success}, Failed: {failed}")
