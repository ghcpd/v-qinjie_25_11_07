from flask import Flask, request, jsonify
from markupsafe import escape
import sqlite3
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Load API key from environment for security
API_KEY = os.environ.get('API_KEY')


def query_users_by_name(name):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Use parameterized query to avoid SQL injection
    sql = "SELECT id, username FROM users WHERE username LIKE ?"
    cur.execute(sql, ('%'+name+'%',))
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Accept only JSON to avoid unsafe pickling
    profile = request.get_json(silent=True)
    if not isinstance(profile, dict):
        return jsonify({"status": "error", "message": "Invalid profile format"}), 400
    return jsonify({"status": "ok", "name": profile.get("name")})


# Only allow whitelisted commands
ALLOWED_COMMANDS = {'echo'}

@app.route('/run', methods=['POST'])
def run_command():
    cmd = request.form.get('cmd', '')
    parts = cmd.split()
    if not parts or parts[0] not in ALLOWED_COMMANDS:
        return jsonify({"status": "error", "message": "Command not allowed"}), 400
    # Use os.spawn to avoid shell injection and pass arguments safely
    try:
        pid = os.spawnlp(os.P_WAIT, parts[0], *parts)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "ok", "exit_code": pid})


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Use escape to prevent XSS
    return f"<h1>Hello {escape(name)}</h1>"


# Store hashed passwords in memory for demo purposes
USERS = {
    "alice": {"password": generate_password_hash("password123")},
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = USERS.get(username)
    if user and check_password_hash(user.get("password"), password):
        return "login ok"
    return "login failed"

if __name__ == '__main__':
    # Do not run with debug=True in production
    app.run(debug=False)
