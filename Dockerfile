FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY input_fixed.py app.py
COPY run_test.sh .

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=False
ENV API_KEY=docker-default-key

# Run tests on container startup
CMD ["bash", "run_test.sh"]
