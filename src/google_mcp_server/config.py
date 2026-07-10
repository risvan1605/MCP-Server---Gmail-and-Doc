"""Configuration and settings for the Google MCP Server.

Loads environment variables from a .env file and defines constants
such as Google API scopes and file paths for credentials/tokens.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from the project root (if it exists)
load_dotenv()


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Base directory — defaults to the current working directory
BASE_DIR = Path(os.getenv("GOOGLE_MCP_BASE_DIR", Path.cwd()))

# Google OAuth credentials file (downloaded from Google Cloud Console)
CREDENTIALS_PATH = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", BASE_DIR / "credentials.json"))

# Cached OAuth token (created after first successful authentication)
TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", BASE_DIR / "token.json"))


# ---------------------------------------------------------------------------
# Google API Scopes
# ---------------------------------------------------------------------------

SCOPES = [
    # Gmail — compose (draft + send) and read-only (get drafts)
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    # Google Docs — full read/write access
    "https://www.googleapis.com/auth/documents",
]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# ---------------------------------------------------------------------------
# Server metadata
# ---------------------------------------------------------------------------

SERVER_NAME = "Google Workspace MCP Server"
SERVER_VERSION = "0.1.0"
