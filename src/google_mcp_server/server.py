"""Google Workspace MCP Server — main entry point.

Creates a FastMCP server instance, registers Gmail and Google Docs tools,
configures logging, and starts the server on stdio transport.
"""

import logging

from mcp.server.fastmcp import FastMCP

from google_mcp_server.config import LOG_LEVEL, SERVER_NAME, SERVER_VERSION
from google_mcp_server.docs.tools import register_docs_tools
from google_mcp_server.gmail.tools import register_gmail_tools
from google_mcp_server.utils.errors import setup_logging

logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """Create and configure the MCP server with all tools registered.

    Returns:
        Configured FastMCP server instance ready to run.
    """
    # Initialize logging (must be stderr for stdio transport)
    setup_logging(LOG_LEVEL)

    logger.info("Initializing %s v%s", SERVER_NAME, SERVER_VERSION)

    # Create the FastMCP server
    mcp = FastMCP(SERVER_NAME)

    # Register tool modules
    register_gmail_tools(mcp)
    register_docs_tools(mcp)

    logger.info("Server initialized with all tools registered")

    return mcp


def main() -> None:
    """Entry point — create the server and run on stdio transport."""
    server = create_server()

    logger.info("Starting server on stdio transport...")
    server.run()


if __name__ == "__main__":
    main()
