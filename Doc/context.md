# Project Context: Generic MCP Server for Gmail & Google Docs

## Overview

This project builds a **Generic Model Context Protocol (MCP) Server** that wraps Gmail and Google Docs APIs into standardized MCP tools. Any MCP-compatible AI agent — Claude, ChatGPT, Cursor, VS Code agents, or custom agents — can discover and invoke these tools to interact with a user's Google Workspace, without implementing any Google-specific integration logic themselves.

---

## Core Problem

AI agents today must each build their own Google API integrations (auth, API calls, error handling). This project eliminates that duplication by providing a single, standards-based MCP server that sits between AI agents and Google Workspace.

```
┌─────────────┐     MCP Protocol     ┌──────────────┐     Google APIs     ┌──────────────────┐
│  AI Agents   │ ◄──────────────────► │  MCP Server  │ ◄────────────────► │ Google Workspace │
│ (Claude,     │   (standardized)     │  (this repo) │   (OAuth 2.0)      │ (Gmail, Docs)    │
│  ChatGPT,    │                      └──────────────┘                    └──────────────────┘
│  Cursor...)  │
└─────────────┘
```

---

## MCP Tools to Implement

### Gmail Tools

| Tool             | Description                                          | Status   |
|------------------|------------------------------------------------------|----------|
| `draft_email`    | Create a new draft with To, CC, BCC, Subject, Body   | Required |
| `update_draft`   | Modify an existing draft                             | Required |
| `send_email`     | Send an email (directly or from a draft)             | Required |
| `get_draft`      | Retrieve a draft by ID                               | Optional |

**Email fields supported:** To, CC, BCC, Subject, Body (plain text & HTML), Attachments (future).

### Google Docs Tools

| Tool                    | Description                                     | Status   |
|-------------------------|-------------------------------------------------|----------|
| `create_document`       | Create a new Google Doc with title and content   | Required |
| `read_document`         | Read the full content of a Google Doc by ID      | Required |
| `append_to_document`    | Append content without overwriting existing text | Required |
| `get_document_metadata` | Retrieve doc metadata (title, URL, etc.)         | Optional |

---

## Authentication

- **Protocol:** OAuth 2.0 with Google Workspace
- **Token management:** Secure storage + automatic refresh
- **Multi-account:** Support for multiple user accounts
- **Isolation:** No credentials embedded in AI agents — all auth is handled server-side

---

## Architecture Principles

| Principle              | Detail                                                                 |
|------------------------|------------------------------------------------------------------------|
| MCP-compliant          | Fully adheres to the Model Context Protocol specification              |
| Platform-agnostic      | Works with any MCP-compatible client, not tied to a specific AI vendor |
| Structured responses   | All tool responses are structured JSON                                 |
| Internal error handling| Auth, retries, and API errors are handled within the server            |
| Modular & extensible   | Easy to add Google Sheets, Drive, Calendar, Slides, Tasks later        |

---

## Non-Functional Requirements

- **Security:** Secure credential management (no plaintext secrets)
- **Logging:** Comprehensive request/response and error logging
- **Error handling:** Graceful failures with meaningful error messages
- **Scalability:** Architecture supports scaling beyond a single user
- **Documentation:** Well-documented tool schemas, config steps, and deployment guide

---

## Key Use Cases

### 1. Send an Email
> Agent instruction: *"Send an email to john@example.com summarizing today's meeting."*

Flow: Agent → `send_email` MCP tool → Gmail API → email delivered.

### 2. Append Meeting Notes
> Agent instruction: *"Append today's discussion to the Project Notes Google Doc."*

Flow: Agent → `append_to_document` MCP tool → Google Docs API → content appended.

---

## Expected Deliverables

| Deliverable                     | Description                                          |
|---------------------------------|------------------------------------------------------|
| MCP Server                      | Core server implementing the MCP protocol            |
| Gmail MCP Tools                 | Draft, update, send, (get) email tools               |
| Google Docs MCP Tools           | Create, read, append, (get metadata) document tools  |
| OAuth Module                    | Authentication & token management                    |
| Configuration Docs              | Setup & configuration instructions                   |
| API/Tool Documentation          | Schema definitions and usage examples                |
| Sample Client Config            | Example MCP client setup for agents                  |
| Deployment Guide                | Docker-based deployment (preferred)                  |

---

## Future Extensibility

The architecture must support adding these Google Workspace services **without breaking existing clients**:

- Google Drive
- Google Sheets
- Google Calendar
- Google Slides
- Google Tasks

---

## Tech Stack Decisions (TBD)

> These decisions should be made during planning:

- **Language/Runtime:** Python (FastAPI/Flask) or Node.js (TypeScript)
- **MCP SDK:** Official MCP SDK or custom implementation
- **Deployment:** Docker container
- **Token Storage:** File-based, SQLite, or cloud secret manager
- **Testing:** Unit tests + integration tests with Google API sandbox
