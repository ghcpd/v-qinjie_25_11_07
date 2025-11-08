#!/bin/bash

# Flask Security Audit - Setup Script for Linux/macOS
# This script sets up the environment for testing the Flask application

set -e

echo "=== Flask Security Audit Setup ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/Scripts/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create test database
echo "Setting up test database..."
python3 -c "
import sqlite3
conn = sqlite3.connect('users.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('INSERT OR REPLACE INTO users (id, username) VALUES (1, \"admin\")')
cur.execute('INSERT OR REPLACE INTO users (id, username) VALUES (2, \"testuser\")')
cur.execute('INSERT OR REPLACE INTO users (id, username) VALUES (3, \"alice\")')
conn.commit()
conn.close()
print('Test database created successfully')
"

# Set environment variables
export API_KEY="test_api_key_for_demo"
export FLASK_ENV="development"

echo ""
echo "=== Setup Complete ==="
echo "Environment is ready for testing."
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  ./run_test.sh"
echo ""