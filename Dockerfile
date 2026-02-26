# syntax=docker/dockerfile:1.7

############################
# Base image and metadata
############################
FROM python:3.12-slim AS base

LABEL org.opencontainers.image.title="financial-analytics-api" \
      org.opencontainers.image.description="FastAPI + Pandas + SQLAlchemy analytics API" \
      org.opencontainers.image.source="https://example.com/docreader" \
      org.opencontainers.image.licenses="MIT"

# Environment variables that improve Python behavior in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

############################
# Builder stage
############################
FROM base AS builder

# Install build dependencies used by scientific Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build wheels in an isolated directory for deterministic and faster installs.
RUN pip wheel --wheel-dir /wheels -r requirements.txt

############################
# Runtime stage
############################
FROM base AS runtime

# Minimal runtime libraries only.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for better container security.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

COPY app ./app
COPY rag ./rag
COPY README.md ./README.md

# Prepare app-owned state directories.
RUN mkdir -p /app/data /app/logs && chown -R appuser:appgroup /app

USER appuser

# FastAPI (uvicorn) default port.
EXPOSE 8000

# Helpful healthcheck for orchestration systems.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# Use tini as PID 1 to forward signals and reap zombie processes.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
