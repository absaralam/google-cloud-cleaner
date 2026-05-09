# Google Cloud Cleaner

Compares files in a local folder against your **Google Drive** and/or **Google Photos** by filename + extension, then deletes the cloud copies to free up space — keeping your local copy safe.

---

## How it works

1. Scans your local folder and builds a list of `(filename stem, extension)` pairs.
2. Fetches your full Google Drive / Google Photos file list via the official Google APIs.
3. Finds cloud files whose name + extension match a local file.
4. Shows you the matches (dry-run preview).
5. Deletes the matched files from the cloud **only after your confirmation**.

---

## Project structure

```
google-cloud-cleaner/
├── main.py                  ← Entry point, run this
├── config.py                ← Optional default settings
├── requirements.txt         ← Python dependencies
├── credentials.json         ← ⬅ YOU must add this (see Step 1 below)
├── token.pickle             ← Auto-created after first login
└── modules/
    ├── auth.py              ← OAuth2 authentication
    ├── local_scanner.py     ← Scans local folder
    ├── drive_handler.py     ← Google Drive API (list + delete)
    └── photos_handler.py    ← Google Photos API (list + report)
```

---

## Setup

### Step 1 — Get Google API credentials

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Create a new project (or select an existing one).
3. Go to **APIs & Services → Library** and enable:
   - **Google Drive API**
   - **Photos Library API**
4. Go to **APIs & Services → OAuth consent screen**:
   - Choose **External** → Fill in app name (anything, e.g. "Cloud Cleaner") → Save.
   - Add your Gmail as a **Test user**.
5. Go to **APIs & Services → Credentials**:
   - Click **+ Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Download the JSON file and rename it to `credentials.json`
   - Place it in the `google-cloud-cleaner/` folder.

### Step 2 — Install Python dependencies

Open a terminal (PowerShell or Command Prompt) in the project folder:

```powershell
pip install -r requirements.txt
```

> Requires Python 3.8+. Check with: `python --version`

### Step 3 — Run the script

**Preview mode (safe — no deletions):**
```powershell
python main.py --local "C:\Users\YourName\Pictures" --service drive
```

**Check both Drive and Photos:**
```powershell
python main.py --local "C:\Users\YourName\Pictures" --service both
```

**Execute real deletion (after reviewing dry-run output):**
```powershell
python main.py --local "C:\Users\YourName\Pictures" --service drive --execute
```

**Non-recursive (top-level folder only):**
```powershell
python main.py --local "C:\Users\YourName\Pictures" --service drive --no-recursive
```

On first run, a browser window will open asking you to log in with your Google account and grant permissions. This only happens once — the token is cached in `token.pickle`.

---

## All CLI options

| Flag              | Description                                               | Default         |
|-------------------|-----------------------------------------------------------|-----------------|
| `--local`         | Path to your local folder (**required**)                  | —               |
| `--service`       | `drive`, `photos`, or `both`                              | `both`          |
| `--execute`       | Perform actual deletion (without this = dry-run preview)  | off (dry-run)   |
| `--no-recursive`  | Don't scan subdirectories                                 | off (recursive) |
| `--credentials`   | Path to `credentials.json`                                | script folder   |
| `--token`         | Path to cached `token.pickle`                             | script folder   |
| `--report-dir`    | Where to save the Google Photos match report CSV          | script folder   |

---

## Google Photos limitation ⚠️

Google's Photos Library API **does not allow deleting photos** that weren't uploaded by the same app. This is a Google restriction — there's no workaround via the official API.

**What the script does instead for Photos:**
- Identifies all matching photos and prints them.
- Exports a **CSV report** (`photos_matches_TIMESTAMP.csv`) with direct `product_url` links.
- Open that CSV and use the links to visit each photo on [photos.google.com](https://photos.google.com) and delete them manually.

For Google Drive, **full automatic deletion** works without restrictions.

---

## Safety notes

- The script runs in **dry-run mode by default** — it will never delete anything unless you pass `--execute`.
- Even with `--execute`, you must type `YES` at the confirmation prompt before anything is deleted.
- Deletion on Drive **skips the Trash** (permanent). Make sure your local copies are intact before executing.
- Matching is done by **name + extension only**. If two different files happen to share a name, both would be flagged. Review the dry-run output carefully before executing.

---

## Re-authenticating

If you ever get authentication errors, delete `token.pickle` and run the script again — it will re-open the browser login flow.
