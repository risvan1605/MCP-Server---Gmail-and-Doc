"""Gmail API wrapper functions.

Low-level functions that interact directly with the Gmail API.
These are called by the MCP tool definitions in tools.py.
"""

import base64
import logging
from email.message import EmailMessage
from typing import Any

from google_mcp_server.auth.oauth import get_gmail_service

logger = logging.getLogger(__name__)


def _build_mime_message(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
) -> EmailMessage:
    """Build an RFC 2822 compliant email message.

    Args:
        to: Recipient email address(es), comma-separated.
        subject: Email subject line.
        body: Email body content.
        cc: CC recipients, comma-separated.
        bcc: BCC recipients, comma-separated.
        body_type: "plain" for plain text, "html" for HTML content.

    Returns:
        Constructed EmailMessage object.
    """
    message = EmailMessage()

    if body_type == "html":
        message.set_content(body, subtype="html")
    else:
        message.set_content(body)

    message["To"] = to
    message["Subject"] = subject

    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc

    return message


def _encode_message(message: EmailMessage) -> str:
    """Base64url-encode an email message for the Gmail API."""
    return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")


def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
) -> dict[str, Any]:
    """Create a new email draft in Gmail.

    Args:
        to: Recipient email address(es), comma-separated.
        subject: Email subject line.
        body: Email body content.
        cc: CC recipients, comma-separated.
        bcc: BCC recipients, comma-separated.
        body_type: "plain" or "html".

    Returns:
        Dict with draft_id, message_id, and a summary of the draft.

    Raises:
        HttpError: If the Gmail API request fails.
    """
    service = get_gmail_service()
    message = _build_mime_message(to, subject, body, cc, bcc, body_type)
    encoded = _encode_message(message)

    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": encoded}})
        .execute()
    )

    logger.info("Created draft %s", draft["id"])

    return {
        "draft_id": draft["id"],
        "message_id": draft["message"]["id"],
        "to": to,
        "subject": subject,
        "body_type": body_type,
    }


def update_draft(
    draft_id: str,
    to: str = "",
    subject: str = "",
    body: str = "",
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
) -> dict[str, Any]:
    """Update an existing email draft.

    Replaces the draft's message content entirely. Fields that are not
    provided (empty string) will be taken from the original draft.

    Args:
        draft_id: ID of the draft to update.
        to: New recipient(s), or empty to keep existing.
        subject: New subject, or empty to keep existing.
        body: New body, or empty to keep existing.
        cc: New CC, or empty to keep existing.
        bcc: New BCC, or empty to keep existing.
        body_type: "plain" or "html".

    Returns:
        Dict with updated draft details.

    Raises:
        HttpError: If the Gmail API request fails.
    """
    service = get_gmail_service()

    # Fetch the existing draft to preserve unchanged fields
    existing = service.users().drafts().get(userId="me", id=draft_id, format="full").execute()
    existing_headers = {}
    if "message" in existing and "payload" in existing["message"]:
        for header in existing["message"]["payload"].get("headers", []):
            existing_headers[header["name"].lower()] = header["value"]

    # Merge: use new values if provided, otherwise keep existing
    final_to = to or existing_headers.get("to", "")
    final_subject = subject or existing_headers.get("subject", "")
    final_cc = cc or existing_headers.get("cc", "")
    final_bcc = bcc or existing_headers.get("bcc", "")

    # For body, if not provided, we can't easily extract the original from
    # the raw message, so we require it for updates
    if not body:
        # Try to decode existing body
        payload = existing.get("message", {}).get("payload", {})
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            body = base64.urlsafe_b64decode(body_data).decode("utf-8")
        else:
            # Check parts for multipart messages
            for part in payload.get("parts", []):
                if part.get("mimeType") in ("text/plain", "text/html"):
                    part_data = part.get("body", {}).get("data", "")
                    if part_data:
                        body = base64.urlsafe_b64decode(part_data).decode("utf-8")
                        break

    message = _build_mime_message(final_to, final_subject, body, final_cc, final_bcc, body_type)
    encoded = _encode_message(message)

    updated = (
        service.users()
        .drafts()
        .update(userId="me", id=draft_id, body={"message": {"raw": encoded}})
        .execute()
    )

    logger.info("Updated draft %s", draft_id)

    return {
        "draft_id": updated["id"],
        "message_id": updated["message"]["id"],
        "to": final_to,
        "subject": final_subject,
        "body_type": body_type,
    }


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
) -> dict[str, Any]:
    """Send an email directly (without creating a draft first).

    Args:
        to: Recipient email address(es), comma-separated.
        subject: Email subject line.
        body: Email body content.
        cc: CC recipients, comma-separated.
        bcc: BCC recipients, comma-separated.
        body_type: "plain" or "html".

    Returns:
        Dict with message_id and label IDs.

    Raises:
        HttpError: If the Gmail API request fails.
    """
    service = get_gmail_service()
    message = _build_mime_message(to, subject, body, cc, bcc, body_type)
    encoded = _encode_message(message)

    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded})
        .execute()
    )

    logger.info("Sent email %s to %s", sent["id"], to)

    return {
        "message_id": sent["id"],
        "thread_id": sent.get("threadId", ""),
        "label_ids": sent.get("labelIds", []),
        "to": to,
        "subject": subject,
    }


def send_draft(draft_id: str) -> dict[str, Any]:
    """Send an existing draft.

    Args:
        draft_id: ID of the draft to send.

    Returns:
        Dict with sent message details.

    Raises:
        HttpError: If the Gmail API request fails.
    """
    service = get_gmail_service()

    sent = (
        service.users()
        .drafts()
        .send(userId="me", body={"id": draft_id})
        .execute()
    )

    logger.info("Sent draft %s as message %s", draft_id, sent["id"])

    return {
        "message_id": sent["id"],
        "thread_id": sent.get("threadId", ""),
        "label_ids": sent.get("labelIds", []),
    }


def get_draft(draft_id: str) -> dict[str, Any]:
    """Retrieve a draft by ID.

    Args:
        draft_id: ID of the draft to retrieve.

    Returns:
        Dict with draft details including headers and body snippet.

    Raises:
        HttpError: If the Gmail API request fails.
    """
    service = get_gmail_service()

    draft = (
        service.users()
        .drafts()
        .get(userId="me", id=draft_id, format="full")
        .execute()
    )

    # Extract useful header information
    headers = {}
    if "message" in draft and "payload" in draft["message"]:
        for header in draft["message"]["payload"].get("headers", []):
            name = header["name"].lower()
            if name in ("to", "from", "subject", "cc", "bcc", "date"):
                headers[name] = header["value"]

    logger.info("Retrieved draft %s", draft_id)

    return {
        "draft_id": draft["id"],
        "message_id": draft["message"]["id"],
        "headers": headers,
        "snippet": draft["message"].get("snippet", ""),
    }
