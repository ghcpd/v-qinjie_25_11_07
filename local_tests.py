"""
Local test runner using Flask test clients to avoid network issues.
"""
import importlib
import sys
import json
import os

# Set API_KEY for secure app before importing
os.environ['API_KEY'] = 'test_api_key_for_demo'

results = {
    'vulnerable': {},
    'secure': {}
}

# Mode selection via command-line argument: 'vulnerable', 'secure', or 'both' (default)
# Optional second argument selects which app to test for secure checks: 'original' or 'repaired'
mode = 'both'
test_target = 'repaired'
if len(sys.argv) > 1:
    mode = sys.argv[1].lower()
if len(sys.argv) > 2:
    test_target = sys.argv[2].lower()  # 'original' or 'repaired'

# Load vulnerable app
vuln_mod = importlib.import_module('input')
app_vuln = vuln_mod.app
client_vuln = app_vuln.test_client()

# Load secure app
secure_mod = importlib.import_module('input_secure')
app_secure = secure_mod.app
client_secure = app_secure.test_client()

if mode in ('both', 'vulnerable'):
    print('Testing vulnerable app...')
    # Basic functionality
    resp = client_vuln.get('/greet?name=test')
    results['vulnerable']['basic'] = (resp.status_code == 200)
    
    # SQL injection: Expect success in vulnerable version (returns users list)
    resp = client_vuln.get("/search?name=test' OR '1'='1")
    results['vulnerable']['sql_injection'] = 'admin' in (resp.get_data(as_text=True) or '')
    
    # Template injection: Expect executed value
    resp = client_vuln.get('/greet?name={{7*7}}')
    results['vulnerable']['template_injection'] = '49' in (resp.get_data(as_text=True) or '')
    
    # Command injection: POST /run
    resp = client_vuln.post('/run', data={'cmd': 'echo test'})
    results['vulnerable']['command_injection'] = resp.status_code == 200
    
    print(json.dumps(results['vulnerable'], indent=2))

if mode in ('both', 'secure'):
    print('\nTesting secure app...')
    # Choose which app to test against for secure checks
    if test_target == 'original':
        client = client_vuln
    else:
        client = client_secure
    
    # Basic functionality
    resp = client.get('/greet?name=test')
    results['secure']['basic'] = (resp.status_code == 200)
    
    # SQL injection protection -> should not contain admin
    resp = client.get("/search?name=test' OR '1'='1")
    try:
        data = resp.get_json()
        users = json.dumps(data.get('users', []))
    except Exception:
        users = resp.get_data(as_text=True)
    results['secure']['sql_protection'] = 'admin' not in (users or '')
    
    # Template injection protected
    resp = client.get('/greet?name={{7*7}}')
    results['secure']['template_protection'] = '{{7*7}}' in resp.get_data(as_text=True) and '49' not in resp.get_data(as_text=True)
    
    # Auth required
    resp = client.post('/run', data={'cmd': 'echo test'})
    results['secure']['auth_required'] = (resp.status_code == 401)
    
    # Valid auth
    resp = client.post('/run', headers={'X-API-Key': 'test_api_key_for_demo'}, data={'cmd': 'echo test'})
    results['secure']['valid_auth'] = (resp.status_code == 200)
    
    # Command not allowed (e.g., 'rm -rf /')
    resp = client.post('/run', headers={'X-API-Key': 'test_api_key_for_demo'}, data={'cmd': 'rm -rf /'})
    results['secure']['command_protection'] = (resp.status_code == 403)
    
    print(json.dumps(results['secure'], indent=2))


# Summarize
vuln_passes = sum(1 for k, v in results['vulnerable'].items() if v)
secure_passes = sum(1 for k, v in results['secure'].items() if v)
print('\nSummary:')
print(f"Vulnerable app vulnerabilities found: {vuln_passes}/{len(results['vulnerable'])} (expected more)")
print(f"Secure app pass rate: {secure_passes}/{len(results['secure'])}")

if mode == 'vulnerable':
    # Pass if at least one vulnerability found
    if vuln_passes > 0:
        print('Vulnerable checks succeeded (vulnerabilities present)')
        sys.exit(0)
    else:
        print('No vulnerabilities detected in vulnerable app (unexpected)')
        sys.exit(1)
elif mode == 'secure':
    # Pass only if all secure tests pass
    if secure_passes == len(results['secure']):
        print('All secure tests passed')
        sys.exit(0)
    else:
        print('One or more secure tests failed')
        sys.exit(1)
else:
    # both: require secure pass all and vulnerable have at least one vuln
    if secure_passes == len(results['secure']) and vuln_passes > 0:
        print('Secure tests all passed and vulnerabilities detected in vulnerable app')
        sys.exit(0)
    else:
        print('Test conditions not met')
        sys.exit(1)

