FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY input.py input_secure.py ./
COPY test_security.py ./

# Create logs directory
RUN mkdir -p logs

# Set environment variables for security
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV API_KEY=test_api_key_for_demo
ENV SECRET_KEY=your_secret_key_here

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Default command (can be overridden)
CMD ["python", "input_secure.py"]