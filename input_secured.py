from flask import Flask, request, render_template_string, jsonify, escape
import sqlite3
import os
import json
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# API key should be loaded from environment variable, not hardcoded
API_KEY = os.environ.get('API_KEY', '')


def query_users_by_name(name):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Use parameterized queries to prevent SQL injection
    sql = "SELECT id, username FROM users WHERE username LIKE ?"
    cur.execute(sql, ('%' + name + '%',))
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Use JSON instead of pickle to prevent remote code execution
    try:
        if request.is_json:
            profile = request.get_json()
        else:
            profile = json.loads(request.data.decode('utf-8'))
        # Validate that profile is a dict
        if not isinstance(profile, dict):
            return jsonify({"status": "error", "message": "Invalid profile format"}), 400
        return jsonify({"status": "ok", "name": profile.get("name")})
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return jsonify({"status": "error", "message": "Invalid JSON format"}), 400


@app.route('/run', methods=['POST'])
def run_command():
    cmd = request.form.get('cmd', '')
    # Use subprocess with proper argument handling instead of os.system
    import subprocess
    try:
        # Only allow specific whitelisted commands or use a command mapping
        # For demonstration, we'll use subprocess.run with shell=False
        # In production, implement a command whitelist
        result = subprocess.run(['echo', 'Running:', cmd], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.stdout if result.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        return "timeout", 408
    except Exception as e:
        return f"error: {str(e)}", 500


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Escape user input to prevent template injection
    safe_name = escape(name)
    template = "<h1>Hello {{ name }}</h1>"
    return render_template_string(template, name=safe_name)


# Initialize users with hashed passwords
# In production, this should be loaded from a database
USERS = {
    "alice": {"password_hash": generate_password_hash("password123")},
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = USERS.get(username)
    # Use password hashing instead of plain text comparison
    if user and check_password_hash(user.get("password_hash"), password):
        return "login ok"
    return "login failed", 401


if __name__ == '__main__':
    # Disable debug mode in production
    app.run(debug=False, host='0.0.0.0', port=5000)

