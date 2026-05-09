"""
main.py — Google Cloud Cleaner
================================
Compares a local folder against Google Drive / Google Photos by
filename + extension, then removes the cloud copies to free up space.

Usage
-----
  # Dry run (safe preview — no deletions):
  python main.py --local "C:\\Users\\You\\Pictures" --service drive

  # Execute real deletion after reviewing dry-run output:
  python main.py --local "C:\\Users\\You\\Pictures" --service drive --execute

  # Check both Drive and Photos:
  python main.py --local "C:\\Users\\You\\Pictures" --service both

  # Non-recursive (top-level folder only):
  python main.py --local "C:\\Users\\You\\Pictures" --service drive --no-recursive
"""

import argparse
import sys
import os

# ── resolve the script's own directory so imports work from any cwd ──────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from modules.auth          import get_credentials
from modules.local_scanner import scan_local_folder, summarize_local
from modules.drive_handler import (
    build_drive_service,
    list_drive_files,
    find_drive_matches,
    print_drive_matches,
    delete_drive_files,
)
from modules.photos_handler import (
    list_photos_media,
    find_photos_matches,
    print_photos_matches,
    export_photos_report,
)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare a local folder with Google Drive/Photos and clean up cloud duplicates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--local", "-l",
        required=True,
        metavar="FOLDER",
        help="Path to the local folder to compare against the cloud.",
    )
    parser.add_argument(
        "--service", "-s",
        choices=["drive", "photos", "both"],
        default="both",
        help="Which Google service to check. Default: both",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually delete cloud duplicates. Without this flag the script runs in safe dry-run mode.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        default=False,
        help="Only scan the top-level of --local (don't walk subdirectories).",
    )
    parser.add_argument(
        "--credentials",
        default=os.path.join(SCRIPT_DIR, "credentials.json"),
        metavar="FILE",
        help="Path to your Google OAuth credentials.json. Default: credentials.json in script folder.",
    )
    parser.add_argument(
        "--token",
        default=os.path.join(SCRIPT_DIR, "token.pickle"),
        metavar="FILE",
        help="Path to cache the OAuth token. Default: token.pickle in script folder.",
    )
    parser.add_argument(
        "--report-dir",
        default=SCRIPT_DIR,
        metavar="DIR",
        help="Directory to save the Google Photos match report CSV. Default: script folder.",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Confirmation helper
# ─────────────────────────────────────────────────────────────────────────────

def confirm_deletion(service_name: str, count: int) -> bool:
    print(f"\n{'='*60}")
    print(f"  ⚠️  You are about to PERMANENTLY DELETE {count} file(s)")
    print(f"      from your Google {service_name}.")
    print(f"  This action CANNOT be undone (files skip the Trash).")
    print(f"{'='*60}")
    answer = input("  Type  YES  to confirm deletion, anything else to cancel: ").strip()
    return answer == "YES"


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args      = parse_args()
    dry_run   = not args.execute
    recursive = not args.no_recursive

    print("\n" + "="*60)
    print("  Google Cloud Cleaner")
    print("="*60)
    print(f"  Local folder : {args.local}")
    print(f"  Service      : {args.service}")
    print(f"  Mode         : {'DRY RUN (safe preview)' if dry_run else '⚠️  EXECUTE — will delete!'}")
    print(f"  Recursive    : {recursive}")
    print("="*60 + "\n")

    # ── 1. Scan local folder ─────────────────────────────────────────────────
    print("[STEP 1] Scanning local folder...")
    local_index = scan_local_folder(args.local, recursive=recursive)
    summarize_local(local_index)

    if not local_index:
        print("[INFO] No local files found. Nothing to compare. Exiting.")
        sys.exit(0)

    # ── 2. Authenticate ──────────────────────────────────────────────────────
    print("\n[STEP 2] Authenticating with Google...")
    creds = get_credentials(
        credentials_file=args.credentials,
        token_file=args.token,
    )
    print("[AUTH] Authentication successful.\n")

    # ── 3. Google Drive ──────────────────────────────────────────────────────
    if args.service in ("drive", "both"):
        print("[STEP 3a] Comparing with Google Drive...")
        drive_service = build_drive_service(creds)
        drive_files   = list_drive_files(drive_service)
        drive_matches = find_drive_matches(drive_files, local_index)
        print_drive_matches(drive_matches)

        if drive_matches:
            if dry_run:
                delete_drive_files(drive_service, drive_matches, dry_run=True)
            else:
                if confirm_deletion("Drive", len(drive_matches)):
                    delete_drive_files(drive_service, drive_matches, dry_run=False)
                else:
                    print("[DRIVE] Deletion cancelled by user.")

    # ── 4. Google Photos ─────────────────────────────────────────────────────
    if args.service in ("photos", "both"):
        print("[STEP 3b] Comparing with Google Photos...")
        media_items    = list_photos_media(creds)
        photos_matches = find_photos_matches(media_items, local_index)
        print_photos_matches(photos_matches)

        if photos_matches:
            # Export CSV report (Photos API can't bulk-delete arbitrary items)
            export_photos_report(photos_matches, output_dir=args.report_dir)

    print("\n[DONE] All steps complete.\n")


if __name__ == "__main__":
    main()
