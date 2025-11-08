from flask import Flask, request, render_template_string, jsonify
from markupsafe import escape
import sqlite3
import os
import json
import hashlib
import secrets
import logging
from functools import wraps
import subprocess
import shlex

app = Flask(__name__)

# Use environment variable for API key
API_KEY = os.environ.get('API_KEY', '')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Generate a secret key for Flask sessions
app.secret_key = secrets.token_hex(32)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Read API_KEY from the environment at request time to allow dynamic updates
        api_key_value = os.environ.get('API_KEY', '')
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != api_key_value:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def query_users_by_name(name):
    """Secure database query using parameterized statements"""
    if not name or len(name) > 50:  # Input validation
        return []
    
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    try:
        # Use parameterized query to prevent SQL injection
        sql = "SELECT id, username FROM users WHERE username LIKE ?"
        cur.execute(sql, (f'%{name}%',))
        rows = cur.fetchall()
    except Exception as e:
        logger.error(f"Database error: {e}")
        rows = []
    finally:
        conn.close()
    return rows

@app.route('/upload_profile', methods=['POST'])
@require_auth
def upload_profile():
    """Secure profile upload using JSON instead of pickle"""
    try:
        # Use JSON instead of pickle for safe deserialization
        content_type = request.headers.get('Content-Type', '')
        if content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # Validate and sanitize profile data
        name = data.get("name", "").strip()
        if not name or len(name) > 100:
            return jsonify({"error": "Invalid name"}), 400
        
        # Additional validation for name (only alphanumeric and spaces)
        if not name.replace(' ', '').isalnum():
            return jsonify({"error": "Name can only contain letters, numbers, and spaces"}), 400
        
        return jsonify({"status": "ok", "name": name})
    except Exception as e:
        logger.error(f"Profile upload error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/run', methods=['POST'])
@require_auth
def run_command():
    """Secure command execution with allowlist"""
    cmd = request.form.get('cmd', '').strip()
    
    # Log request details for debugging
    logger.info(f"Run request headers: {request.headers}")
    logger.info(f"Requested cmd: {cmd}")
    
    # Whitelist of allowed commands
    allowed_commands = ['echo', 'date', 'pwd']
    
    if not cmd:
        return jsonify({"error": "No command provided"}), 400
    
    # Parse command safely
    try:
        cmd_parts = shlex.split(cmd)
        if not cmd_parts or cmd_parts[0] not in allowed_commands:
            return jsonify({"error": "Command not allowed"}), 403
        
        # Execute safe, mapped commands without shell to avoid command injection
        action = cmd_parts[0]
        if action == 'echo':
            output = ' '.join(cmd_parts[1:]) + '\n'
            return jsonify({"status": "ok", "output": output, "error": ""})
        elif action == 'date':
            from datetime import datetime
            return jsonify({"status": "ok", "output": datetime.utcnow().isoformat() + '\n', "error": ""})
        elif action == 'pwd':
            return jsonify({"status": "ok", "output": os.getcwd() + '\n', "error": ""})
        else:
            return jsonify({"error": "Command not implemented"}), 501
    except Exception as e:
        logger.exception("Command execution error")
        return jsonify({"error": "Command execution failed"}), 500

@app.route('/search')
def search_users():
    """Secure user search endpoint"""
    name = request.args.get('name', '')
    
    if not name:
        return jsonify({"error": "Name parameter required"}), 400
    
    try:
        users = query_users_by_name(name)
        return jsonify({"users": users})
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/greet')
def greet():
    """Secure template rendering with proper escaping"""
    name = request.args.get('name', 'guest')
    
    # Input validation
    if len(name) > 50:
        name = 'guest'
    
    # Use Jinja's escape filter to prevent XSS/template injection
    logger.info(f"Raw name: {name}")
    
    # Use a safe template and apply escaping in template
    template = "<h1>Hello {{ name | e }}</h1>"
    return render_template_string(template, name=name)

# Secure user storage with hashed passwords
def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(32)
    return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt

def verify_password(stored_password, provided_password):
    """Verify password against stored hash"""
    try:
        hash_part, salt = stored_password.split(':')
        return hash_part == hashlib.sha256((provided_password + salt).encode()).hexdigest()
    except:
        return False

# Users with hashed passwords (in production, use a proper database)
USERS = {
    "alice": {
        "password": hash_password("secure_password_123!"),
        "role": "user"
    },
}

@app.route('/login', methods=['POST'])
def login():
    """Secure login with proper password hashing"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    if len(username) > 50 or len(password) > 128:
        return jsonify({"error": "Invalid credentials"}), 400
    
    user = USERS.get(username)
    if user and verify_password(user.get("password", ""), password):
        logger.info(f"Successful login for user: {username}")
        return jsonify({"status": "login ok", "message": "Authentication successful"})
    
    logger.warning(f"Failed login attempt for user: {username}")
    return jsonify({"error": "Invalid credentials"}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Disable debug mode for production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='127.0.0.1')