# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies to /opt/venv
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Set PATH to use venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user and set ownership
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app /opt/venv
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

# Start application
CMD ["python", "app.py"]
