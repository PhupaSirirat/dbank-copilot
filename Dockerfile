# Dockerfile
# Multi-stage build for dBank Copilot

# ============================================
# Base Stage - Common dependencies
# ============================================
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# ============================================
# Runtime Stage - For running services
# ============================================
FROM base AS runtime

# Create non-root user for security
RUN useradd -m -u 1000 dbank && \
    chown -R dbank:dbank /app

USER dbank

# Expose ports
EXPOSE 8000 8001

# Default command (overridden by docker-compose)
CMD ["python", "--version"]

# ============================================
# Development Stage - With dev tools
# ============================================
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython

# Keep as root for development
USER root

CMD ["bash"]