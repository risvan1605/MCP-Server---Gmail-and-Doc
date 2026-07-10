# Google Workspace MCP Server

A generic **Model Context Protocol (MCP) Server** that exposes Gmail and Google Docs as standardized tools, enabling any MCP-compatible AI agent (Claude, ChatGPT, Cursor, VS Code agents, etc.) to securely interact with Google Workspace.

## Features

- **Gmail Tools** — Draft, update, send, and retrieve emails
- **Google Docs Tools** — Create, read, append to, and inspect documents
- **OAuth 2.0** — Secure authentication with automatic token refresh
- **MCP-Compliant** — Works with any MCP client out of the box
- **Structured Responses** — Consistent JSON response envelopes for all tools
- **Extensible** — Modular architecture for adding Google Sheets, Drive, Calendar, etc.

## Prerequisites

- Python 3.11+
- A Google Cloud project with Gmail API and Google Docs API enabled
- OAuth 2.0 credentials (`credentials.json`)

## Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Enable **Gmail API** and **Google Docs API**
5. Navigate to **APIs & Services → Credentials**
6. Click **Create Credentials → OAuth 2.0 Client ID**
7. Select **Desktop app** as the application type
8. Download the credentials file and save it as `credentials.json` in the project root
9. Navigate to **OAuth consent screen** and add your email as a test user

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd google-mcp-server

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install the package
pip install -e .

# Install dev dependencies (optional)
pip install -e ".[dev]"
```

## Configuration

Copy the environment template and configure:

```bash
cp .env.example .env
```

Edit `.env` as needed:

```env
GOOGLE_CREDENTIALS_PATH=./credentials.json
GOOGLE_TOKEN_PATH=./token.json
LOG_LEVEL=INFO
```

## First Run

On the first run, the server will open your browser for Google OAuth consent:

```bash
python -m google_mcp_server.server
```

1. A browser window will open asking you to sign in to Google
2. Grant the requested permissions (Gmail compose/read, Google Docs read/write)
3. The token is saved to `token.json` for future use
4. The server starts on stdio transport, ready for MCP client connections

## Available Tools

### Gmail

| Tool | Description |
|------|-------------|
| `draft_email` | Create a new email draft with To, CC, BCC, Subject, and Body |
| `update_email_draft` | Update an existing draft (unchanged fields are preserved) |
| `send_new_email` | Send an email directly without creating a draft |
| `send_existing_draft` | Send a previously created draft |
| `get_email_draft` | Retrieve a draft by ID with headers and snippet |

### Google Docs

| Tool | Description |
|------|-------------|
| `create_google_doc` | Create a new document with optional initial content |
| `read_google_doc` | Read the full text content of a document |
| `append_to_google_doc` | Append text to the end of a document |
| `get_google_doc_metadata` | Get document metadata (title, revision, URL) |

## MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "python",
      "args": ["-m", "google_mcp_server.server"],
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "/absolute/path/to/credentials.json",
        "GOOGLE_TOKEN_PATH": "/absolute/path/to/token.json"
      }
    }
  }
}
```

### Cursor

Add to your MCP settings:

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "python",
      "args": ["-m", "google_mcp_server.server"],
      "cwd": "/path/to/google-mcp-server"
    }
  }
}
```

### VS Code (Copilot)

Add to your VS Code settings:

```json
{
  "mcp": {
    "servers": {
      "google-workspace": {
        "command": "python",
        "args": ["-m", "google_mcp_server.server"],
        "cwd": "/path/to/google-mcp-server"
      }
    }
  }
}
```

## Vercel Deployment

This MCP server is configured for serverless deployment on Vercel using Server-Sent Events (SSE).

1. Push your code to a GitHub repository.
2. Go to the [Vercel Dashboard](https://vercel.com/) and create a new project from your repository.
3. In the environment variables section, add the following variable:
   - Key: `GOOGLE_TOKEN_JSON`
   - Value: (Paste the exact contents of your local `token.json` file)
4. Also add:
   - Key: `VERCEL`
   - Value: `1`
5. Deploy the project!

Once deployed, your MCP SSE endpoint will be available at:
`https://<your-vercel-domain>/sse`

Clients connecting to a Vercel-deployed server must use the SSE transport configuration instead of the stdio transport.

## Testing with MCP Inspector

Use the official MCP Inspector to test your server interactively:

```bash
npx -y @modelcontextprotocol/inspector python -m google_mcp_server.server
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/google_mcp_server --cov-report=term-missing

# Lint
ruff check src/ tests/
```

## Docker

```bash
# Build
docker build -f docker/Dockerfile -t google-mcp-server .

# Run (mount your credentials)
docker run -it \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  google-mcp-server
```

## Project Structure

```
google-mcp-server/
├── pyproject.toml                # Project config & dependencies
├── .env.example                  # Environment variable template
├── credentials.json              # Google OAuth credentials (gitignored)
├── token.json                    # Cached OAuth token (gitignored)
├── src/
│   └── google_mcp_server/
│       ├── server.py             # FastMCP server entry point
│       ├── config.py             # Settings & environment loading
│       ├── auth/
│       │   └── oauth.py          # OAuth 2.0 flow & token management
│       ├── gmail/
│       │   ├── service.py        # Gmail API wrapper functions
│       │   └── tools.py          # Gmail MCP tool definitions
│       ├── docs/
│       │   ├── service.py        # Google Docs API wrapper functions
│       │   └── tools.py          # Docs MCP tool definitions
│       └── utils/
│           └── errors.py         # Error handling & response formatting
├── tests/                        # Unit tests
└── docker/
    └── Dockerfile                # Docker deployment
```

## License

MIT
