"""Standardized error handling and response formatting.

All MCP tool responses pass through these helpers to ensure a consistent
JSON structure for both success and error cases.
"""

import logging
import sys
from typing import Any

from googleapiclient.errors import HttpError

# Configure logging to stderr (stdout is reserved for MCP stdio transport)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response formatters
# ---------------------------------------------------------------------------

def format_success(data: dict[str, Any], message: str = "Operation completed successfully") -> dict:
    """Wrap a successful result in a consistent JSON envelope.

    Args:
        data: The result payload.
        message: Optional human-readable success message.

    Returns:
        Standardized success response dict.
    """
    return {
        "status": "success",
        "message": message,
        "data": data,
    }


def format_error(error: Exception, context: str = "") -> dict:
    """Wrap an error in a consistent JSON envelope.

    Maps common Google API HTTP errors to user-friendly messages.

    Args:
        error: The exception that occurred.
        context: Additional context about what operation was being performed.

    Returns:
        Standardized error response dict.
    """
    error_type = type(error).__name__
    error_message = str(error)

    # Map common Google API errors to helpful messages
    if isinstance(error, HttpError):
        status_code = error.resp.status
        error_message = _map_http_error(status_code, error_message, context)
        error_type = f"HttpError_{status_code}"
    elif isinstance(error, FileNotFoundError):
        error_type = "ConfigurationError"
    elif isinstance(error, RuntimeError):
        error_type = "AuthenticationError"

    logger.error("Error in %s: [%s] %s", context or "unknown operation", error_type, error_message)

    return {
        "status": "error",
        "error_type": error_type,
        "message": error_message,
        "context": context,
    }


def _map_http_error(status_code: int, original_message: str, context: str) -> str:
    """Map HTTP status codes to user-friendly error messages."""
    error_map = {
        400: f"Bad request — check your input parameters. {context}",
        401: (
            "Authentication expired or invalid. "
            "Delete token.json and re-run the server to re-authenticate."
        ),
        403: (
            "Insufficient permissions. Ensure the Google Cloud project has the required APIs "
            "enabled and the OAuth scopes include the necessary permissions."
        ),
        404: f"Resource not found. {context}. Verify the ID is correct and accessible.",
        429: "Rate limited by Google API. Please wait a moment and try again.",
        500: "Google API internal server error. Please try again later.",
        503: "Google API service temporarily unavailable. Please try again later.",
    }
    return error_map.get(status_code, f"Google API error ({status_code}): {original_message}")


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO") -> None:
    """Configure logging to write to stderr.

    This is critical for MCP servers using stdio transport — any output
    to stdout would corrupt the JSON-RPC communication channel.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logger.info("Logging configured at %s level (stderr)", level)
