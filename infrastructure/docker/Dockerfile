FROM python:3.11-slim

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY infrastructure/requirements/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py interfaces.py encryption.py ./
COPY src/ ./src/

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app
ENV WORKERS=4
ENV TIMEOUT=120

# Expose port
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Create app factory function for Gunicorn
RUN echo "from main import get_app; app = get_app()" > wsgi.py

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "wsgi:app"]
