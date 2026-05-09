"""
config.py — Optional defaults you can edit instead of passing CLI flags every time.

These values are used only if you import and call get_defaults() from main.py.
CLI arguments always take priority over these defaults.
"""

# ── Local folder to scan ──────────────────────────────────────────────────────
# Change this to your default local folder, e.g.:
#   LOCAL_FOLDER = r"C:\Users\YourName\Pictures"
#   LOCAL_FOLDER = r"D:\Backups\Photos"
LOCAL_FOLDER = r"C:\Users\YourName\Pictures"

# ── Which service to check: "drive", "photos", or "both" ─────────────────────
SERVICE = "both"

# ── Recurse into subdirectories? ──────────────────────────────────────────────
RECURSIVE = True

# ── Default mode: set to False to enable real deletion by default ─────────────
#    It's strongly recommended to leave this True and use --execute on the CLI.
DRY_RUN = True


def get_defaults() -> dict:
    return {
        "local":     LOCAL_FOLDER,
        "service":   SERVICE,
        "recursive": RECURSIVE,
        "dry_run":   DRY_RUN,
    }
