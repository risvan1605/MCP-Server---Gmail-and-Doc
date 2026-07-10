"""MCP tool definitions for Google Docs.

Each function decorated with @mcp.tool() becomes a discoverable MCP tool
that AI agents can invoke. Tools delegate to the service layer and wrap
results in standardized response envelopes.
"""

import logging

from mcp.server.fastmcp import FastMCP

from google_mcp_server.docs.service import (
    append_to_document,
    create_document,
    get_document_metadata,
    read_document,
)
from google_mcp_server.utils.errors import format_error, format_success

logger = logging.getLogger(__name__)


def register_docs_tools(mcp: FastMCP) -> None:
    """Register all Google Docs MCP tools on the given FastMCP server instance.

    Args:
        mcp: The FastMCP server to register tools on.
    """

    @mcp.tool()
    def create_google_doc(title: str, content: str = "") -> dict:
        """Create a new Google Document.

        Args:
            title: The title of the new document.
            content: Optional initial text content to add to the document body.

        Returns:
            Document ID, title, and URL on success, or error details on failure.
        """
        try:
            if not title:
                return format_error(
                    ValueError("'title' is required"),
                    context="create_google_doc",
                )
            result = create_document(title, content)
            return format_success(
                result, message=f"Document '{title}' created successfully"
            )
        except Exception as exc:
            return format_error(exc, context="create_google_doc")

    @mcp.tool()
    def read_google_doc(document_id: str) -> dict:
        """Read the full content of a Google Document.

        Extracts all text content from the document, preserving paragraph structure.

        Args:
            document_id: The ID of the Google Document to read (found in the document URL).

        Returns:
            Document ID, title, full text content, and URL.
        """
        try:
            if not document_id:
                return format_error(
                    ValueError("'document_id' is required"),
                    context="read_google_doc",
                )
            result = read_document(document_id)
            return format_success(
                result, message=f"Document '{result['title']}' read successfully"
            )
        except Exception as exc:
            return format_error(exc, context="read_google_doc")

    @mcp.tool()
    def append_to_google_doc(document_id: str, content: str) -> dict:
        """Append content to the end of an existing Google Document.

        The content is added after the existing text without overwriting anything.

        Args:
            document_id: The ID of the Google Document to append to.
            content: The text content to append to the document.

        Returns:
            Document ID, title, number of characters appended, and URL.
        """
        try:
            if not document_id or not content:
                return format_error(
                    ValueError("'document_id' and 'content' are required"),
                    context="append_to_google_doc",
                )
            result = append_to_document(document_id, content)
            return format_success(
                result,
                message=f"Appended {result['appended_length']} chars to '{result['title']}'",
            )
        except Exception as exc:
            return format_error(exc, context="append_to_google_doc")

    @mcp.tool()
    def get_google_doc_metadata(document_id: str) -> dict:
        """Get metadata for a Google Document.

        Retrieves the document's title, revision ID, URL, and page size
        without reading the full content.

        Args:
            document_id: The ID of the Google Document.

        Returns:
            Document metadata including title, revision, and URL.
        """
        try:
            if not document_id:
                return format_error(
                    ValueError("'document_id' is required"),
                    context="get_google_doc_metadata",
                )
            result = get_document_metadata(document_id)
            return format_success(
                result, message=f"Metadata for '{result['title']}' retrieved successfully"
            )
        except Exception as exc:
            return format_error(exc, context="get_google_doc_metadata")

    logger.info("Registered %d Google Docs MCP tools", 4)
