# Base stage: Python with essential tools
FROM python:3.14-alpine AS base

RUN apk add --no-cache \
    openssl \
    ca-certificates

# Build stage: Install dependencies and build
FROM base AS build

RUN apk add --no-cache \
    curl \
    build-base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files and required files for build
COPY pyproject.toml uv.lock README.md LICENSE.md ./
COPY src ./src

# Install dependencies
RUN uv sync --frozen --no-dev

# Build the package
RUN uv build

# Final stage: Minimal runtime
FROM base AS final

WORKDIR /app

# Copy uv from build stage
COPY --from=build /usr/local/bin/uv /usr/local/bin/uv

# Copy Python environment from build stage
COPY --from=build /app/.venv /app/.venv

# Copy built package
COPY --from=build /app/dist/*.whl /tmp/

# Install the package
RUN uv pip install --python /app/.venv/bin/python /tmp/*.whl && rm /tmp/*.whl

ENV PATH="/app/.venv/bin:$PATH"

# Default command (override in specific Dockerfiles)
CMD ["mcp-guide", "--help"]
