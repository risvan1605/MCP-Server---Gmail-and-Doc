"""Tests for Google Docs service and MCP tools."""

from unittest.mock import MagicMock, patch

from google_mcp_server.docs.service import (
    _extract_text_from_body,
    append_to_document,
    create_document,
    get_document_metadata,
    read_document,
)


class TestExtractTextFromBody:
    """Tests for the text extraction helper."""

    def test_empty_body(self):
        """Should return empty string for an empty body."""
        result = _extract_text_from_body({})
        assert result == ""

    def test_single_paragraph(self):
        """Should extract text from a single paragraph."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Hello World\n"}}
                        ]
                    }
                }
            ]
        }
        result = _extract_text_from_body(body)
        assert result == "Hello World\n"

    def test_multiple_paragraphs(self):
        """Should concatenate text from multiple paragraphs."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "First paragraph\n"}}
                        ]
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Second paragraph\n"}}
                        ]
                    }
                },
            ]
        }
        result = _extract_text_from_body(body)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_paragraph_with_multiple_runs(self):
        """Should concatenate multiple text runs within a paragraph."""
        body = {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Bold "}},
                            {"textRun": {"content": "and normal\n"}},
                        ]
                    }
                }
            ]
        }
        result = _extract_text_from_body(body)
        assert result == "Bold and normal\n"


class TestCreateDocument:
    """Tests for the create_document service function."""

    @patch("google_mcp_server.docs.service.get_docs_service")
    def test_create_without_content(self, mock_get_service):
        """Should create a document with just a title."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.documents().create().execute.return_value = {
            "documentId": "doc_123",
        }

        result = create_document("My Document")

        assert result["document_id"] == "doc_123"
        assert result["title"] == "My Document"
        assert "doc_123" in result["url"]
        # batchUpdate should NOT be called when no content is provided
        mock_service.documents().batchUpdate.assert_not_called()

    @patch("google_mcp_server.docs.service.get_docs_service")
    def test_create_with_content(self, mock_get_service):
        """Should create a document and insert initial content."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.documents().create().execute.return_value = {
            "documentId": "doc_456",
        }

        result = create_document("With Content", content="Hello World")

        assert result["document_id"] == "doc_456"
        # batchUpdate SHOULD be called to insert the content
        mock_service.documents().batchUpdate.assert_called_once()


class TestReadDocument:
    """Tests for the read_document service function."""

    @patch("google_mcp_server.docs.service.get_docs_service")
    def test_read_document_success(self, mock_get_service):
        """Should read and extract text from a document."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.documents().get().execute.return_value = {
            "documentId": "doc_123",
            "title": "Test Doc",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Document content\n"}}
                            ]
                        }
                    }
                ]
            },
        }

        result = read_document("doc_123")

        assert result["document_id"] == "doc_123"
        assert result["title"] == "Test Doc"
        assert "Document content" in result["content"]


class TestAppendToDocument:
    """Tests for the append_to_document service function."""

    @patch("google_mcp_server.docs.service.get_docs_service")
    def test_append_to_document_success(self, mock_get_service):
        """Should append content at the end of the document."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.documents().get().execute.return_value = {
            "documentId": "doc_123",
            "title": "Test Doc",
            "body": {
                "content": [
                    {
                        "endIndex": 50,
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Existing content\n"}}
                            ]
                        },
                    }
                ]
            },
        }

        result = append_to_document("doc_123", "New content")

        assert result["document_id"] == "doc_123"
        assert result["appended_length"] == len("New content")
        mock_service.documents().batchUpdate.assert_called_once()


class TestGetDocumentMetadata:
    """Tests for the get_document_metadata service function."""

    @patch("google_mcp_server.docs.service.get_docs_service")
    def test_get_metadata_success(self, mock_get_service):
        """Should return document metadata."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.documents().get().execute.return_value = {
            "documentId": "doc_123",
            "title": "Test Doc",
            "revisionId": "rev_1",
            "documentStyle": {
                "pageSize": {"width": {"magnitude": 612, "unit": "PT"}},
            },
        }

        result = get_document_metadata("doc_123")

        assert result["document_id"] == "doc_123"
        assert result["title"] == "Test Doc"
        assert result["revision_id"] == "rev_1"


class TestDocsMCPToolRegistration:
    """Test that MCP tools are registered correctly."""

    def test_all_docs_tools_registered(self):
        """Should register all 4 Google Docs MCP tools."""
        from mcp.server.fastmcp import FastMCP

        from google_mcp_server.docs.tools import register_docs_tools

        mcp = FastMCP("test")
        register_docs_tools(mcp)

        tool_names = {t.name for t in mcp._tool_manager._tools.values()}
        expected = {
            "create_google_doc",
            "read_google_doc",
            "append_to_google_doc",
            "get_google_doc_metadata",
        }
        assert expected.issubset(tool_names)
