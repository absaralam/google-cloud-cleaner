"""
auth.py — Google OAuth2 authentication
Handles token creation, refresh, and loading for Drive + Photos scopes.
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes needed:
#   Drive: list + delete files
#   Photos: list media items (deletion via API is limited to app-created items)
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/photoslibrary.readonly",
]

TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"


def get_credentials(credentials_file: str = CREDENTIALS_FILE, token_file: str = TOKEN_FILE):
    """
    Load cached credentials or run OAuth flow if needed.
    Returns valid google.oauth2.credentials.Credentials object.
    """
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"\n[ERROR] '{credentials_file}' not found!\n"
                    "Please follow the README to download your OAuth credentials from\n"
                    "Google Cloud Console and place credentials.json in this folder.\n"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
        print(f"[AUTH] Credentials saved to '{token_file}'")

    return creds
