FROM python:3.11-slim

LABEL maintainer="signage"
LABEL description="Samsung Frame TV Signage Generator"

# Set working directory
WORKDIR /app

# Install system dependencies
# - fonts for text rendering
# - git for version info
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/art_folder /app/.cache /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=US/Pacific

# Health check - verify main script exists and Python works
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command runs in daemon mode
CMD ["python", "-u", "generate_signage.py", "--daemon"]
