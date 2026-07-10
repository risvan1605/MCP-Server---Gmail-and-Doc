# --- Build stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only dependency files first for better caching
COPY pyproject.toml ./

# Install build dependencies and the project
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# --- Runtime stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package in the runtime image
RUN pip install --no-cache-dir -e .

# Mount points for credentials (these should be mounted at runtime)
# docker run -v /path/to/credentials.json:/app/credentials.json ...
VOLUME ["/app/credentials.json", "/app/token.json"]

# Environment defaults
ENV GOOGLE_CREDENTIALS_PATH=/app/credentials.json
ENV GOOGLE_TOKEN_PATH=/app/token.json
ENV LOG_LEVEL=INFO

# Run the MCP server
ENTRYPOINT ["python", "-m", "google_mcp_server.server"]
