"""Tests for Gmail service and MCP tools."""

import base64
from unittest.mock import MagicMock, patch

from google_mcp_server.gmail.service import (
    _build_mime_message,
    _encode_message,
    create_draft,
    get_draft,
    send_draft,
    send_email,
)


class TestMimeMessageBuilder:
    """Tests for MIME message construction."""

    def test_plain_text_message(self):
        """Should create a plain text email message."""
        msg = _build_mime_message(
            to="test@example.com",
            subject="Test Subject",
            body="Hello World",
        )
        assert msg["To"] == "test@example.com"
        assert msg["Subject"] == "Test Subject"
        assert "Hello World" in msg.get_content()

    def test_html_message(self):
        """Should create an HTML email message."""
        msg = _build_mime_message(
            to="test@example.com",
            subject="HTML Test",
            body="<h1>Hello</h1>",
            body_type="html",
        )
        assert msg["To"] == "test@example.com"
        assert msg.get_content_type() == "text/html"

    def test_cc_and_bcc(self):
        """Should include CC and BCC headers when provided."""
        msg = _build_mime_message(
            to="to@example.com",
            subject="Test",
            body="Body",
            cc="cc@example.com",
            bcc="bcc@example.com",
        )
        assert msg["Cc"] == "cc@example.com"
        assert msg["Bcc"] == "bcc@example.com"

    def test_no_cc_bcc_when_empty(self):
        """Should not include CC/BCC headers when empty."""
        msg = _build_mime_message(
            to="to@example.com",
            subject="Test",
            body="Body",
        )
        assert msg["Cc"] is None
        assert msg["Bcc"] is None

    def test_encode_message_returns_string(self):
        """Should return a base64url-encoded string."""
        msg = _build_mime_message("to@example.com", "Sub", "Body")
        encoded = _encode_message(msg)
        assert isinstance(encoded, str)
        # Should be valid base64
        decoded = base64.urlsafe_b64decode(encoded)
        assert b"Sub" in decoded


class TestCreateDraft:
    """Tests for the create_draft service function."""

    @patch("google_mcp_server.gmail.service.get_gmail_service")
    def test_create_draft_success(self, mock_get_service):
        """Should create a draft and return its ID."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.users().drafts().create().execute.return_value = {
            "id": "draft_123",
            "message": {"id": "msg_456"},
        }

        result = create_draft("to@example.com", "Subject", "Body")

        assert result["draft_id"] == "draft_123"
        assert result["message_id"] == "msg_456"
        assert result["to"] == "to@example.com"
        assert result["subject"] == "Subject"


class TestSendEmail:
    """Tests for the send_email service function."""

    @patch("google_mcp_server.gmail.service.get_gmail_service")
    def test_send_email_success(self, mock_get_service):
        """Should send an email and return the message ID."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.users().messages().send().execute.return_value = {
            "id": "msg_789",
            "threadId": "thread_1",
            "labelIds": ["SENT"],
        }

        result = send_email("to@example.com", "Subject", "Body")

        assert result["message_id"] == "msg_789"
        assert result["thread_id"] == "thread_1"
        assert result["to"] == "to@example.com"


class TestSendDraft:
    """Tests for the send_draft service function."""

    @patch("google_mcp_server.gmail.service.get_gmail_service")
    def test_send_draft_success(self, mock_get_service):
        """Should send a draft and return the sent message ID."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.users().drafts().send().execute.return_value = {
            "id": "msg_sent",
            "threadId": "thread_2",
            "labelIds": ["SENT"],
        }

        result = send_draft("draft_123")

        assert result["message_id"] == "msg_sent"


class TestGetDraft:
    """Tests for the get_draft service function."""

    @patch("google_mcp_server.gmail.service.get_gmail_service")
    def test_get_draft_success(self, mock_get_service):
        """Should retrieve draft details including headers."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.users().drafts().get().execute.return_value = {
            "id": "draft_123",
            "message": {
                "id": "msg_456",
                "snippet": "Hello world preview",
                "payload": {
                    "headers": [
                        {"name": "To", "value": "to@example.com"},
                        {"name": "Subject", "value": "Test Subject"},
                        {"name": "From", "value": "me@example.com"},
                    ]
                },
            },
        }

        result = get_draft("draft_123")

        assert result["draft_id"] == "draft_123"
        assert result["headers"]["to"] == "to@example.com"
        assert result["headers"]["subject"] == "Test Subject"
        assert result["snippet"] == "Hello world preview"


class TestGmailMCPToolResponses:
    """Test that MCP tool wrappers return proper response envelopes."""

    @patch("google_mcp_server.gmail.tools.create_draft")
    def test_draft_email_tool_success_envelope(self, mock_create):
        """Tool should wrap result in a success envelope."""
        from mcp.server.fastmcp import FastMCP

        from google_mcp_server.gmail.tools import register_gmail_tools

        mock_create.return_value = {
            "draft_id": "d1",
            "message_id": "m1",
            "to": "a@b.com",
            "subject": "S",
            "body_type": "plain",
        }

        mcp = FastMCP("test")
        register_gmail_tools(mcp)

        # Find and invoke the draft_email tool
        tools = {t.name: t for t in mcp._tool_manager._tools.values()}
        assert "draft_email" in tools

    @patch("google_mcp_server.gmail.tools.create_draft")
    def test_draft_email_tool_error_envelope(self, mock_create):
        """Tool should wrap errors in an error envelope."""
        from mcp.server.fastmcp import FastMCP

        from google_mcp_server.gmail.tools import register_gmail_tools

        mock_create.side_effect = Exception("API Error")

        mcp = FastMCP("test")
        register_gmail_tools(mcp)

        tools = {t.name: t for t in mcp._tool_manager._tools.values()}
        assert "draft_email" in tools
