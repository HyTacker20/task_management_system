# Build stage
FROM python:3.12-slim AS builder

# Build-time environment (dev or prod)
ARG ENV=dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Create and set work directory
WORKDIR /app

# Install Python dependencies using uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Optionally install development/test dependencies when ENV=dev
COPY requirements-dev.txt ./requirements-dev.txt
RUN if [ "$ENV" = "dev" ]; then uv pip install --system -r requirements-dev.txt; fi

# Runtime stage
FROM python:3.12-slim


# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django && \
    mkdir -p /app && \
    chown -R django:django /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set work directory
WORKDIR /app

# Copy project files
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Run Django development server (override in production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
