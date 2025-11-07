import sys
import os
import platform
import subprocess
import json

LOG_FILE = os.path.join('logs', 'test_run.log')

print('Detected platform:', platform.system())

mode = 'fixed'
if len(sys.argv) > 1 and sys.argv[1] in ('fixed', 'original'):
    mode = sys.argv[1]

print('Test mode:', mode)

# If testing original, temporarily replace input.py with input_original.py
backup = None
if mode == 'original':
    with open('input.py', 'r', encoding='utf-8') as f:
        backup = f.read()
    with open('input_original.py', 'r', encoding='utf-8') as f:
        orig = f.read()
    with open('input.py', 'w', encoding='utf-8') as f:
        f.write(orig)

try:
    cmd = [sys.executable, '-m', 'pytest', '-q']
    result = subprocess.run(cmd)
finally:
    if mode == 'original' and backup is not None:
        with open('input.py', 'w', encoding='utf-8') as f:
            f.write(backup)

if result.returncode == 0:
    print('Tests passed')
    sys.exit(0)
else:
    print('Tests failed')
    sys.exit(result.returncode)
