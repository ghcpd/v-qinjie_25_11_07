from flask import Flask, request, render_template, jsonify, abort
import sqlite3
import subprocess
import json
import os
import hashlib
import hmac

app = Flask(__name__)

# Use environment variables for sensitive config
APP_SECRET = os.environ.get('APP_SECRET', None)
if not APP_SECRET:
    # Do not default to a hardcoded secret in production
    APP_SECRET = None


def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


def query_users_by_name(name):
    conn = get_db_connection()
    cur = conn.cursor()
    # Use parameterized query to prevent SQL injection
    sql = "SELECT id, username FROM users WHERE username LIKE ?"
    cur.execute(sql, (f"%{name}%",))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Do not accept pickle. Accept JSON only and validate.
    try:
        profile = request.get_json(force=True)
    except Exception:
        abort(400, "Invalid JSON")
    if not isinstance(profile, dict):
        abort(400, "Profile must be a JSON object")
    name = profile.get("name")
    return jsonify({"status": "ok", "name": name})


@app.route('/run', methods=['POST'])
def run_command():
    # Do not run arbitrary shell commands. Accept only whitelisted commands.
    cmd = request.form.get('cmd', '')
    allowed = {"echo": ["Running:"]}
    parts = cmd.split()
    if not parts:
        return "no command", 400
    base = parts[0]
    if base not in allowed:
        return "command not allowed", 403
    # Run using subprocess without shell to avoid injection
    args = parts
    try:
        completed = subprocess.run(args, capture_output=True, text=True, check=True)
        return completed.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr or str(e), 500


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Use Flask templates which escape by default
    return render_template('greet.html', name=name)


# Simple user store with hashed passwords (for demo only). Use a real user DB in prod.
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


USERS = {
    "alice": {"password": hash_password("password123")},
}


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "login failed", 400
    user = USERS.get(username)
    if not user:
        return "login failed", 403
    # Use constant-time comparison
    if hmac.compare_digest(user.get("password"), hash_password(password)):
        return "login ok"
    return "login failed", 403


if __name__ == '__main__':
    # Turn off debug in production; use env var to enable for development
    debug_flag = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_flag)
