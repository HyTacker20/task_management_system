FROM python:3.12-slim

ARG ENV=dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 django && \
    mkdir -p /app /opt/venv && \
    chown -R django:django /app /opt/venv

# Set work directory
WORKDIR /app

# Create virtual environment at /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

# Copy and install dependencies
COPY requirements.txt requirements-dev.txt ./
RUN if [ "$ENV" = "dev" ]; then \
        pip install -r requirements.txt -r requirements-dev.txt; \
    else \
        pip install -r requirements.txt; \
    fi

# Install runtime dependencies only (remove build dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]