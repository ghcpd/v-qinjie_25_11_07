#!/bin/bash

# Setup script for Linux/macOS
# This script sets up the environment for security testing

set -e

echo "=== Security Audit Environment Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 is required"; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv || { echo "Error: Failed to create virtual environment"; exit 1; }

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Create test database
echo "Creating test database..."
python3 << EOF
import sqlite3
conn = sqlite3.connect('users.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users 
               (id INTEGER PRIMARY KEY, username TEXT)''')
cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'testuser')")
cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (2, 'alice')")
conn.commit()
conn.close()
print("Test database created successfully")
EOF

# Initialize secured database if needed
if [ -f "init_secured_db.py" ]; then
    echo "Initializing secured database..."
    python3 init_secured_db.py
fi

# Set API key environment variable
export API_KEY="test_api_key_12345"

echo ""
echo "=== Setup Complete ==="
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To run tests, execute: ./run_test.sh"

