from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import shlex

app = Flask(__name__)

# API_KEY should be loaded from environment variables, not hardcoded
API_KEY = os.environ.get('API_KEY', 'default-dev-key-change-in-production')


def query_users_by_name(name):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Use parameterized queries to prevent SQL injection
    sql = "SELECT id, username FROM users WHERE username LIKE ?"
    cur.execute(sql, (f'%{name}%',))
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    try:
        # Use JSON instead of pickle for safer deserialization
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        profile = data
        # Assume profile is a dict
        return jsonify({"status": "ok", "name": profile.get("name")})
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid request"}), 400


@app.route('/run', methods=['POST'])
def run_command():
    cmd = request.form.get('cmd', '')
    # Use subprocess with argument list instead of string concatenation
    # This prevents shell injection
    try:
        result = subprocess.run(
            ['echo', 'Running:', cmd],
            capture_output=True,
            text=True,
            timeout=5
        )
        return jsonify({"status": "done", "output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timeout"}), 500
    except Exception as e:
        return jsonify({"error": "Command execution failed"}), 500


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Use proper Jinja2 templating with auto-escaping
    # Safe because Jinja2 auto-escapes by default
    template = "<h1>Hello {{ name }}</h1>"
    return render_template_string(template, name=name)


USERS = {
    "alice": {"password": generate_password_hash("secure_password_123")},
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = USERS.get(username)
    if user and check_password_hash(user.get("password", ""), password):
        return jsonify({"status": "login ok"})
    return jsonify({"status": "login failed"}), 401

if __name__ == '__main__':
    # Debug mode should be disabled in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode)
