FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps in production image)
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# MCP server via stdio — no port exposed by default
CMD ["uv", "run", "python", "-m", "contas"]
