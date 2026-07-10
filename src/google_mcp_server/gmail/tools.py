"""MCP tool definitions for Gmail.

Each function decorated with @mcp.tool() becomes a discoverable MCP tool
that AI agents can invoke. Tools delegate to the service layer and wrap
results in standardized response envelopes.
"""

import logging

from mcp.server.fastmcp import FastMCP

from google_mcp_server.gmail.service import (
    create_draft,
    get_draft,
    send_draft,
    send_email,
    update_draft,
)
from google_mcp_server.utils.errors import format_error, format_success

logger = logging.getLogger(__name__)


def register_gmail_tools(mcp: FastMCP) -> None:
    """Register all Gmail MCP tools on the given FastMCP server instance.

    Args:
        mcp: The FastMCP server to register tools on.
    """

    @mcp.tool()
    def draft_email(
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        body_type: str = "plain",
    ) -> dict:
        """Create a new email draft in Gmail.

        Args:
            to: Recipient email address (comma-separated for multiple recipients).
            subject: Email subject line.
            body: Email body content.
            cc: CC recipients (comma-separated, optional).
            bcc: BCC recipients (comma-separated, optional).
            body_type: Content type — "plain" for plain text or "html" for HTML content.

        Returns:
            Draft ID, message ID, and a summary of the created draft.
        """
        try:
            if not to or not subject:
                return format_error(
                    ValueError("'to' and 'subject' are required fields"),
                    context="draft_email",
                )
            result = create_draft(to, subject, body, cc, bcc, body_type)
            msg = f"Draft created successfully (ID: {result['draft_id']})"
            return format_success(result, message=msg)
        except Exception as exc:
            return format_error(exc, context="draft_email")

    @mcp.tool()
    def update_email_draft(
        draft_id: str,
        to: str = "",
        subject: str = "",
        body: str = "",
        cc: str = "",
        bcc: str = "",
        body_type: str = "plain",
    ) -> dict:
        """Update an existing email draft in Gmail.

        Only provide the fields you want to change — unchanged fields will
        be preserved from the original draft.

        Args:
            draft_id: The ID of the draft to update.
            to: New recipient(s), or leave empty to keep existing.
            subject: New subject, or leave empty to keep existing.
            body: New body content, or leave empty to keep existing.
            cc: New CC recipients, or leave empty to keep existing.
            bcc: New BCC recipients, or leave empty to keep existing.
            body_type: Content type — "plain" or "html".

        Returns:
            Updated draft details or error information.
        """
        try:
            if not draft_id:
                return format_error(
                    ValueError("'draft_id' is required"),
                    context="update_email_draft",
                )
            result = update_draft(draft_id, to, subject, body, cc, bcc, body_type)
            return format_success(result, message=f"Draft {draft_id} updated successfully")
        except Exception as exc:
            return format_error(exc, context="update_email_draft")

    @mcp.tool()
    def send_new_email(
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        body_type: str = "plain",
    ) -> dict:
        """Send an email directly via Gmail.

        This sends the email immediately without creating a draft first.

        Args:
            to: Recipient email address (comma-separated for multiple recipients).
            subject: Email subject line.
            body: Email body content.
            cc: CC recipients (comma-separated, optional).
            bcc: BCC recipients (comma-separated, optional).
            body_type: Content type — "plain" for plain text or "html" for HTML content.

        Returns:
            Sent message ID and thread details, or error information.
        """
        try:
            if not to or not subject or not body:
                return format_error(
                    ValueError("'to', 'subject', and 'body' are required fields"),
                    context="send_new_email",
                )
            result = send_email(to, subject, body, cc, bcc, body_type)
            return format_success(result, message=f"Email sent successfully to {to}")
        except Exception as exc:
            return format_error(exc, context="send_new_email")

    @mcp.tool()
    def send_existing_draft(draft_id: str) -> dict:
        """Send an existing email draft via Gmail.

        Args:
            draft_id: The ID of the draft to send.

        Returns:
            Sent message details or error information.
        """
        try:
            if not draft_id:
                return format_error(
                    ValueError("'draft_id' is required"),
                    context="send_existing_draft",
                )
            result = send_draft(draft_id)
            return format_success(result, message=f"Draft {draft_id} sent successfully")
        except Exception as exc:
            return format_error(exc, context="send_existing_draft")

    @mcp.tool()
    def get_email_draft(draft_id: str) -> dict:
        """Retrieve an existing email draft from Gmail.

        Args:
            draft_id: The ID of the draft to retrieve.

        Returns:
            Draft details including headers, snippet, and IDs.
        """
        try:
            if not draft_id:
                return format_error(
                    ValueError("'draft_id' is required"),
                    context="get_email_draft",
                )
            result = get_draft(draft_id)
            return format_success(result, message=f"Draft {draft_id} retrieved successfully")
        except Exception as exc:
            return format_error(exc, context="get_email_draft")

    logger.info("Registered %d Gmail MCP tools", 5)
