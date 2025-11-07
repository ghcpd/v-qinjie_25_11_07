import requests
import subprocess
import json
import os
import pickle

# This script performs simple checks against a running Flask app on localhost:5000
# It returns non-zero exit code on failure. It contains both dynamic tests and
# a static scan for obvious hardcoded secrets to demonstrate differences
# between the original insecure app and the patched app.

BASE = os.environ.get('APP_BASE', 'http://127.0.0.1:5000')

results = {}

# 1) Pickle upload check: send a benign pickled dict. Original app will accept
# and return 200; patched app rejects non-JSON and returns 400.
try:
    payload = pickle.dumps({'name': 'pwn'})
    headers = {'Content-Type': 'application/octet-stream'}
    r = requests.post(f"{BASE}/upload_profile", data=payload, headers=headers, timeout=5)
    if r.status_code == 200 and 'pwn' in r.text:
        results['pickle_check'] = 'vulnerable'
    else:
        results['pickle_check'] = 'ok'
except Exception as e:
    results['pickle_check'] = 'error'

# 2) XSS check: ensure greeting is escaped. Vulnerable app will reflect raw script.
try:
    payload = '<script>alert(1)</script>'
    r = requests.get(f"{BASE}/greet", params={'name': payload}, timeout=5)
    results['xss_check'] = 'vulnerable' if payload in r.text else 'ok'
except Exception:
    results['xss_check'] = 'error'

# 3) Static scan for hardcoded secrets in source files
def scan_for_hardcoded_secrets(path):
    findings = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if 'API_KEY' in line or 'AKIA_' in line or 'PASSWORD' in line:
                findings.append({'file': path, 'line': i, 'content': line.strip()})
    return findings

secrets = []
for p in ['input.py', 'input_original.py']:
    full = os.path.join(os.getcwd(), p)
    if os.path.exists(full):
        secrets.extend(scan_for_hardcoded_secrets(full))

results['hardcoded_secrets'] = secrets

print(json.dumps(results, indent=2))

# Exit with non-zero if vulnerabilities detected (this is used to assert original fails)
if results.get('pickle_check') == 'vulnerable' or results.get('xss_check') == 'vulnerable' or len(secrets) > 0:
    exit(1)
exit(0)
