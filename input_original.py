"""Original insecure Flask app copy for baseline tests."""
from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os
import pickle

app = Flask(__name__)


API_KEY = "AKIA_EXAMPLE_HARDCODED_KEY_123456"


def query_users_by_name(name):
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    # Direct string formatting -> SQL injection
    sql = "SELECT id, username FROM users WHERE username LIKE '%{}%'".format(name)
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    # Directly loading pickled bytes from user -> remote code execution risk
    data = request.data
    profile = pickle.loads(data)
    # Assume profile is a dict
    return jsonify({"status": "ok", "name": profile.get("name")})


@app.route('/run', methods=['POST'])
def run_command():
    cmd = request.form.get('cmd', '')
    # Concatenate user input into shell command
    os.system("echo Running: " + cmd)
    return "done"


@app.route('/greet')
def greet():
    name = request.args.get('name', 'guest')
    # Insert user input into template without escaping
    template = "<h1>Hello %s</h1>" % name
    return render_template_string(template)


USERS = {
    "alice": {"password": "password123"},
}

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = USERS.get(username)
    if user and user.get("password") == password:
        return "login ok"
    return "login failed"

if __name__ == '__main__':
    app.run(debug=True)
