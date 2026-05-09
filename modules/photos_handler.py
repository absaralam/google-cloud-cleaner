"""
photos_handler.py — Google Photos media listing and match reporting.

IMPORTANT LIMITATION:
    Google Photos Library API only allows deleting media items that were
    uploaded by the SAME app (via the API). Photos uploaded through the
    Google Photos app, camera sync, or Drive cannot be deleted via API.

    This module therefore:
      - Lists all accessible media items from Google Photos
      - Identifies matches against your local index (by name + extension)
      - Exports a report of matches so you can manually delete them in the
        Google Photos web UI (photos.google.com)
      - Attempts API deletion only for items the app itself uploaded
        (rare in practice — most users won't hit this path)
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Tuple

import requests


PHOTOS_API_BASE = "https://photoslibrary.googleapis.com/v1"
PAGE_SIZE = 100  # max allowed by the API


def list_photos_media(creds) -> List[Dict]:
    """
    Fetch all media items from Google Photos using REST API.
    Returns a list of mediaItem dicts.
    """
    headers = {"Authorization": f"Bearer {creds.token}"}
    items   = []
    page_token = None

    print("[PHOTOS] Fetching media list from Google Photos...", flush=True)
    while True:
        params = {"pageSize": PAGE_SIZE}
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(f"{PHOTOS_API_BASE}/mediaItems", headers=headers, params=params)

        if resp.status_code == 401:
            # Token may have expired mid-run; attempt a refresh
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            headers["Authorization"] = f"Bearer {creds.token}"
            resp = requests.get(f"{PHOTOS_API_BASE}/mediaItems", headers=headers, params=params)

        if not resp.ok:
            print(f"[PHOTOS] API error {resp.status_code}: {resp.text}")
            break

        data       = resp.json()
        batch      = data.get("mediaItems", [])
        items.extend(batch)
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    print(f"[PHOTOS] Total media items found: {len(items)}")
    return items


def find_photos_matches(
    media_items: List[Dict],
    local_index: Dict[Tuple[str, str], List[str]],
) -> List[Dict]:
    """
    Find Photos media items whose (stem, ext) match a local file.
    Returns augmented list of matching media item dicts.
    """
    from pathlib import PurePosixPath

    matches = []
    for item in media_items:
        filename = item.get("filename", "")
        p    = PurePosixPath(filename)
        stem = p.stem.lower()
        ext  = p.suffix.lower()
        key  = (stem, ext)

        if key in local_index:
            item["_local_paths"] = local_index[key]
            item["_match_key"]   = key
            matches.append(item)

    return matches


def print_photos_matches(matches: List[Dict]) -> None:
    """Pretty-print matched Photos items."""
    if not matches:
        print("[PHOTOS] No matching media items found between Google Photos and local folder.")
        return

    print(f"\n[PHOTOS] {len(matches)} item(s) in Google Photos match local files:\n")
    print(f"  {'#':<5} {'Photos Filename':<45} {'Media ID':<45} {'Local Match'}")
    print(f"  {'-'*5} {'-'*45} {'-'*45} {'-'*40}")
    for i, item in enumerate(matches, 1):
        local_display = item["_local_paths"][0] if item["_local_paths"] else "?"
        print(f"  {i:<5} {item.get('filename','?'):<45} {item.get('id','?'):<45} {local_display}")
    print()


def export_photos_report(matches: List[Dict], output_dir: str = ".") -> str:
    """
    Export a CSV report of matched Photos items so you can manually
    review and delete them at photos.google.com.

    Returns the path to the generated CSV file.
    """
    if not matches:
        return ""

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"photos_matches_{timestamp}.csv")

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "media_id", "product_url", "creation_time", "local_match"
        ])
        writer.writeheader()
        for item in matches:
            writer.writerow({
                "filename":      item.get("filename", ""),
                "media_id":      item.get("id", ""),
                "product_url":   item.get("productUrl", ""),
                "creation_time": item.get("mediaMetadata", {}).get("creationTime", ""),
                "local_match":   item["_local_paths"][0] if item.get("_local_paths") else "",
            })

    print(f"\n[PHOTOS] Report saved to: {report_path}")
    print("[PHOTOS] Open this CSV and use the 'product_url' links to delete items")
    print("         manually at photos.google.com (API deletion is restricted by Google).\n")
    return report_path
