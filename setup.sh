#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create a small sqlite DB for tests
python - <<'PY'
import sqlite3
con = sqlite3.connect('users.db')
cur = con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute("INSERT OR IGNORE INTO users (username) VALUES ('alice')")
con.commit()
con.close()
PY
