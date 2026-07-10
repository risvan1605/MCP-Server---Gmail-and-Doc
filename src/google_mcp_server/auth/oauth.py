"""OAuth 2.0 authentication and Google service builders.

Handles the full OAuth lifecycle:
  1. Load cached token from token.json
  2. Refresh if expired
  3. Run interactive consent flow if no token exists
  4. Persist token after successful auth

Provides factory functions to build authenticated Gmail and Docs API services.
"""

import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from google_mcp_server.config import CREDENTIALS_PATH, SCOPES, TOKEN_PATH

# Use stderr for logging — stdout is reserved for MCP stdio transport
logger = logging.getLogger(__name__)


def get_credentials() -> Credentials:
    """Load, refresh, or create OAuth 2.0 credentials.

    Returns:
        Authenticated Google OAuth 2.0 credentials.

    Raises:
        FileNotFoundError: If credentials.json is missing and no token exists.
        RuntimeError: If the OAuth flow fails.
    """
    creds = None

    # Step 1: Try loading cached token
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            logger.info("Loaded cached token from %s", TOKEN_PATH)
        except Exception as exc:
            logger.warning("Failed to load cached token: %s", exc)
            creds = None

    # Step 2: Refresh expired token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Refreshed expired token")
            _save_token(creds)
        except Exception as exc:
            logger.warning("Token refresh failed, re-authenticating: %s", exc)
            creds = None

    # Step 3: Run interactive OAuth flow if no valid credentials
    if not creds or not creds.valid:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Google OAuth credentials file not found at {CREDENTIALS_PATH}. "
                "Download it from the Google Cloud Console → APIs & Services → Credentials."
            )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Completed OAuth consent flow")
            _save_token(creds)
        except Exception as exc:
            raise RuntimeError(f"OAuth authentication flow failed: {exc}") from exc

    return creds


def _save_token(creds: Credentials) -> None:
    """Persist credentials to token.json for future use."""
    try:
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        logger.info("Saved token to %s", TOKEN_PATH)
    except Exception as exc:
        logger.error("Failed to save token: %s", exc)


# ---------------------------------------------------------------------------
# Service builders
# ---------------------------------------------------------------------------

_gmail_service = None
_docs_service = None


def get_gmail_service():
    """Build and cache an authenticated Gmail API service.

    Returns:
        googleapiclient Resource for Gmail API v1.
    """
    global _gmail_service
    if _gmail_service is None:
        creds = get_credentials()
        _gmail_service = build("gmail", "v1", credentials=creds)
        logger.info("Built Gmail API service")
    return _gmail_service


def get_docs_service():
    """Build and cache an authenticated Google Docs API service.

    Returns:
        googleapiclient Resource for Google Docs API v1.
    """
    global _docs_service
    if _docs_service is None:
        creds = get_credentials()
        _docs_service = build("docs", "v1", credentials=creds)
        logger.info("Built Google Docs API service")
    return _docs_service


def reset_services() -> None:
    """Reset cached services (useful for testing or re-authentication)."""
    global _gmail_service, _docs_service
    _gmail_service = None
    _docs_service = None
    logger.info("Reset cached API services")
