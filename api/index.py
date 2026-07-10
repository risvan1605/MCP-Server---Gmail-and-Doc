"""Vercel serverless function entrypoint.

This file creates the FastMCP server and exposes its ASGI application
so Vercel can route HTTP requests to it using Server-Sent Events (SSE).
"""

from google_mcp_server.server import create_server

# Create the FastMCP server with all tools registered
mcp = create_server()

# Expose the Starlette ASGI application for Vercel.
# This automatically handles the /sse and /messages routes.
app = mcp.sse_app()
