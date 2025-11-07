#!/bin/bash

# setup.sh - Environment setup script for Linux/macOS

set -e

echo "=== Security Audit Environment Setup ==="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Set environment variables
echo "Setting up environment variables..."
export FLASK_ENV=development
export FLASK_DEBUG=False
export FLASK_HOST=127.0.0.1
export FLASK_PORT=5000
export API_KEY=test_api_key_for_demo
export SECRET_KEY=your_secret_key_here

# Create .env file for persistent environment variables
echo "Creating .env file..."
cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=False
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
API_KEY=test_api_key_for_demo
SECRET_KEY=your_secret_key_here
EOF

echo "=== Setup Complete ==="
echo "To activate the environment manually, run: source venv/bin/activate"
echo "To load environment variables, run: source .env"
echo "To run tests, execute: ./run_test.sh"