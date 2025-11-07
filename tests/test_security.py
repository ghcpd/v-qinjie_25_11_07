import io
import pickle
import os
import pytest
from input import app, API_KEY


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_reject_pickled_profile(client):
    # Create a pickled payload that would run arbitrary code if unpickled
    payload = pickle.dumps({'name': 'Attacker'})
    rv = client.post('/upload_profile', data=payload, content_type='application/octet-stream')
    assert rv.status_code == 400


def test_disallow_arbitrary_command(client):
    rv = client.post('/run', data={'cmd': 'ls -la'})
    assert rv.status_code == 400


def test_xss_protection(client):
    xss = '<script>alert(1)</script>'
    rv = client.get(f'/greet?name={xss}')
    assert '<script>' not in rv.get_data(as_text=True)


def test_no_hardcoded_api_key():
    assert API_KEY is None or not str(API_KEY).startswith('AKIA_')
