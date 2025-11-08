from flask import Flask, request, render_template_string, jsonify
from markupsafe import escape
import sqlite3
import os
import json
import hashlib
import secrets
import logging
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secure: Use environment variable for API key
API_KEY = os.environ.get('API_KEY', '')
if not API_KEY:
    logging.warning("API_KEY environment variable not set")

# Secure: Generate random secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

def init_db():
    """Initialize database with secure schema"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                   (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
    # Add a test user with hashed password
    password_hash = generate_password_hash('securepassword123')
    cur.execute('''INSERT OR REPLACE INTO users (username, password_hash) 
                   VALUES (?, ?)''', ('alice', password_hash))
    conn.commit()
    conn.close()

def query_users_by_name(name):
    """Secure: Use parameterized queries to prevent SQL injection"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Secure: Use parameterized query instead of string formatting
    sql = "SELECT id, username FROM users WHERE username LIKE ?"
    cur.execute(sql, (f'%{name}%',))
    rows = cur.fetchall()
    conn.close()
    return rows

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    """Secure: Use JSON instead of pickle for data serialization"""
    try:
        # Secure: Use JSON instead of pickle to prevent code execution
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        profile = request.get_json()
        if not profile or not isinstance(profile, dict):
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Validate and sanitize input
        name = profile.get("name", "")
        if not isinstance(name, str) or len(name) > 100:
            return jsonify({"error": "Invalid name field"}), 400
        
        return jsonify({"status": "ok", "name": escape(name)})
    except Exception as e:
        logging.error(f"Error processing profile upload: {str(e)}")
        return jsonify({"error": "Invalid data format"}), 400

@app.route('/run', methods=['POST'])
def run_command():
    """Secure: Validate and sanitize command input"""
    cmd = request.form.get('cmd', '').strip()
    
    # Secure: Whitelist allowed commands instead of executing arbitrary input
    allowed_commands = ['help', 'status', 'version']
    
    if cmd not in allowed_commands:
        return jsonify({"error": "Command not allowed"}), 400
    
    # Secure: Use predefined responses instead of executing system commands
    responses = {
        'help': 'Available commands: help, status, version',
        'status': 'System is running normally',
        'version': 'Application version 1.0.0'
    }
    
    return jsonify({"result": responses.get(cmd, "Unknown command")})

@app.route('/greet')
def greet():
    """Secure: Escape user input to prevent template injection"""
    name = request.args.get('name', 'guest')
    
    # Secure: Validate input length and characters
    if len(name) > 50:
        name = 'guest'
    
    # Secure: Use escape to prevent template injection
    safe_name = escape(name)
    template = "<h1>Hello {{ name }}</h1>"
    return render_template_string(template, name=safe_name)

def authenticate_user(username, password):
    """Secure: Check credentials against database with hashed passwords"""
    if not username or not password:
        return False
    
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cur.fetchone()
    conn.close()
    
    if result:
        return check_password_hash(result[0], password)
    return False

@app.route('/login', methods=['POST'])
def login():
    """Secure: Use proper authentication with hashed passwords"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if authenticate_user(username, password):
        return jsonify({"status": "login successful"})
    else:
        # Secure: Generic error message to prevent username enumeration
        return jsonify({"error": "Invalid credentials"}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Secure: Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)