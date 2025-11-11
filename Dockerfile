FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY input.py .
COPY input_secured.py .
COPY run_test.sh .

# Create logs directory
RUN mkdir -p logs

# Set environment variable for API key (should be overridden in production)
ENV API_KEY=""

# Expose Flask port
EXPOSE 5000

# Default command runs tests
CMD ["/bin/bash", "run_test.sh"]

