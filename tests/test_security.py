import os
import sqlite3
import pickle
from flask import json
import pytest

import input as fixed
import input_original as original

DB = 'users.db'


def setup_module(module):
    # Create small test DB
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
    cur.execute('DELETE FROM users')
    cur.execute("INSERT INTO users (username) VALUES ('alice')")
    cur.execute("INSERT INTO users (username) VALUES ('bob')")
    conn.commit()
    conn.close()


def teardown_module(module):
    if os.path.exists(DB):
        os.remove(DB)


def test_sql_injection_original():
    # attempt a typical injection that should succeed in the original implementation
    rows = original.query_users_by_name("' OR 1=1 -- ")
    # original should return all rows because of SQL injection
    assert len(rows) >= 2


def test_sql_injection_fixed():
    rows = fixed.query_users_by_name("' OR 1=1 -- ")
    # After parameterization, this will not match all users; it should return 0
    assert len(rows) == 0


def test_pickle_deserialization_original(client=None):
    client = original.app.test_client()
    payload = pickle.dumps({"name": "attacker"})
    r = client.post('/upload_profile', data=payload)
    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'ok'


def test_pickle_deserialization_fixed():
    client = fixed.app.test_client()
    payload = pickle.dumps({"name": "attacker"})
    # fixed should reject non-JSON payloads
    r = client.post('/upload_profile', data=payload)
    assert r.status_code == 400


def test_run_command_original_monkeypatch(monkeypatch):
    executed = {}

    def fake_system(cmd):
        executed['cmd'] = cmd
        return 0

    monkeypatch.setattr(original.os, 'system', fake_system)
    client = original.app.test_client()
    r = client.post('/run', data={'cmd': 'hello; rm -rf /'}, follow_redirects=True)
    assert r.status_code == 200
    assert 'rm -rf' in executed.get('cmd', '')


def test_run_command_fixed(monkeypatch):
    executed = {}

    def fake_system(cmd):
        executed['cmd'] = cmd
        return 0

    monkeypatch.setattr(fixed.os, 'system', fake_system)
    client = fixed.app.test_client()
    r = client.post('/run', data={'cmd': 'echo hello'})
    assert r.status_code == 200
    # The fixed version should not call os.system and instead returns the echo payload
    assert executed == {}
    assert r.get_json()['result'] == 'hello'


def test_xss_original():
    client = original.app.test_client()
    r = client.get('/greet?name=<script>alert(1)</script>')
    assert r.status_code == 200
    assert b'<script>alert(1)</script>' in r.data


def test_xss_fixed():
    client = fixed.app.test_client()
    r = client.get('/greet?name=<script>alert(1)</script>')
    assert r.status_code == 200
    # fixed app should escape the script tag
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in r.data


def test_password_stored_hashed():
    assert original.USERS['alice']['password'] == 'password123'
    assert fixed.USERS['alice']['password'] != 'password123'


def test_debug_flag_default():
    assert fixed.app.debug == False
