"""Google Docs API wrapper functions.

Low-level functions that interact directly with the Google Docs API.
These are called by the MCP tool definitions in tools.py.
"""

import logging
from typing import Any

from google_mcp_server.auth.oauth import get_docs_service

logger = logging.getLogger(__name__)

# Base URL for Google Docs
DOCS_BASE_URL = "https://docs.google.com/document/d"


def create_document(title: str, content: str = "") -> dict[str, Any]:
    """Create a new Google Document.

    Args:
        title: The title of the new document.
        content: Optional initial text content to add to the document body.

    Returns:
        Dict with document_id, title, and URL.

    Raises:
        HttpError: If the Google Docs API request fails.
    """
    service = get_docs_service()

    # Create the document with just a title
    doc = service.documents().create(body={"title": title}).execute()
    document_id = doc["documentId"]

    logger.info("Created document '%s' with ID %s", title, document_id)

    # If initial content is provided, insert it into the document body
    if content:
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},  # Index 1 = start of body
                    "text": content,
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
        logger.info("Inserted initial content into document %s", document_id)

    return {
        "document_id": document_id,
        "title": title,
        "url": f"{DOCS_BASE_URL}/{document_id}/edit",
    }


def read_document(document_id: str) -> dict[str, Any]:
    """Read the full content of a Google Document.

    Extracts all text content from the document body, preserving
    paragraph structure.

    Args:
        document_id: The ID of the Google Document to read.

    Returns:
        Dict with document_id, title, content (plain text), and URL.

    Raises:
        HttpError: If the Google Docs API request fails.
    """
    service = get_docs_service()

    doc = service.documents().get(documentId=document_id).execute()
    title = doc.get("title", "Untitled")

    # Extract text content from the document body
    content = _extract_text_from_body(doc.get("body", {}))

    logger.info("Read document '%s' (%s) — %d chars", title, document_id, len(content))

    return {
        "document_id": document_id,
        "title": title,
        "content": content,
        "url": f"{DOCS_BASE_URL}/{document_id}/edit",
    }


def append_to_document(document_id: str, content: str) -> dict[str, Any]:
    """Append content to the end of a Google Document.

    Inserts a newline followed by the content at the end of the document
    body, preserving all existing content.

    Args:
        document_id: The ID of the Google Document to append to.
        content: The text content to append.

    Returns:
        Dict with document_id, title, appended content length, and URL.

    Raises:
        HttpError: If the Google Docs API request fails.
    """
    service = get_docs_service()

    # First, get the document to find the end-of-body index
    doc = service.documents().get(documentId=document_id).execute()
    title = doc.get("title", "Untitled")

    # The end index of the body content
    body = doc.get("body", {})
    body_content = body.get("content", [])

    if body_content:
        # The last structural element's endIndex gives us the insertion point
        # We subtract 1 because the final newline character is at the end
        end_index = body_content[-1].get("endIndex", 1) - 1
    else:
        end_index = 1

    # Prepend a newline to separate from existing content
    text_to_insert = f"\n{content}"

    requests = [
        {
            "insertText": {
                "location": {"index": end_index},
                "text": text_to_insert,
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=document_id, body={"requests": requests}
    ).execute()

    logger.info(
        "Appended %d chars to document '%s' (%s)", len(content), title, document_id
    )

    return {
        "document_id": document_id,
        "title": title,
        "appended_length": len(content),
        "url": f"{DOCS_BASE_URL}/{document_id}/edit",
    }


def get_document_metadata(document_id: str) -> dict[str, Any]:
    """Retrieve metadata for a Google Document.

    Args:
        document_id: The ID of the Google Document.

    Returns:
        Dict with document_id, title, revision_id, URL, and locale.

    Raises:
        HttpError: If the Google Docs API request fails.
    """
    service = get_docs_service()

    doc = service.documents().get(documentId=document_id).execute()

    logger.info("Retrieved metadata for document %s", document_id)

    return {
        "document_id": doc["documentId"],
        "title": doc.get("title", "Untitled"),
        "revision_id": doc.get("revisionId", ""),
        "url": f"{DOCS_BASE_URL}/{doc['documentId']}/edit",
        "document_style": {
            "page_size": doc.get("documentStyle", {}).get("pageSize", {}),
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text_from_body(body: dict) -> str:
    """Extract plain text from a Google Docs body structure.

    The body contains a list of structural elements (paragraphs, tables, etc.).
    We walk through them and concatenate all text runs.

    Args:
        body: The document body dict from the Docs API response.

    Returns:
        Concatenated plain text content.
    """
    text_parts = []

    for element in body.get("content", []):
        if "paragraph" in element:
            paragraph = element["paragraph"]
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))
        elif "table" in element:
            # Extract text from table cells
            table = element["table"]
            for row in table.get("tableRows", []):
                for cell in row.get("tableCells", []):
                    cell_text = _extract_text_from_body(cell)
                    if cell_text.strip():
                        text_parts.append(cell_text)

    return "".join(text_parts)
