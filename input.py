from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)


# API key should never be hardcoded. Load from environment for security.
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    # Fail fast if the key is required for operation — do not use a default secret
    API_KEY = None


def query_users_by_name(name):
    # Use parameterized queries to avoid SQL injection
    conn = sqlite3.connect('users.db')
    try:
        cur = conn.cursor()
        sql = "SELECT id, username FROM users WHERE username LIKE ?"
        cur.execute(sql, (f"%{name}%",))
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Accept only JSON to avoid insecure deserialization
    if not request.is_json:
        return jsonify({"status": "error", "reason": "JSON required"}), 400
    profile = request.get_json()
    if not isinstance(profile, dict):
        return jsonify({"status": "error", "reason": "Invalid payload"}), 400
    # Basic validation
    name = profile.get('name')
    if not isinstance(name, str) or len(name) > 256:
        return jsonify({"status": "error", "reason": "Invalid name"}), 400
    return jsonify({"status": "ok", "name": name})


@app.route('/run', methods=['POST'])
def run_command():
    # Do not execute arbitrary shell commands. Implement a command whitelist or safe operations.
    cmd = request.form.get('cmd', '')
    if not isinstance(cmd, str) or len(cmd) > 256:
        return "invalid command", 400
    # Very small safe subset: only allow echo-like behavior
    if cmd.startswith('echo '):
        payload = cmd[len('echo '):]
        # no shell, just return the text
        return jsonify({"status": "ok", "result": payload})
    return "command not allowed", 403


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Use Jinja2 autoescaping by passing the value as a context variable
    template = "<h1>Hello {{ name }}</h1>"
    return render_template_string(template, name=name)


from werkzeug.security import generate_password_hash, check_password_hash

# Store only password hashes
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
    # Do not enable debug by default; leave explicit enabling to the environment.
    debug_flag = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true')
    app.run(debug=debug_flag)
