import platform
import subprocess
import os

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

if platform.system() == 'Windows':
    cmd = ['cmd', '/c', 'run_test.bat']
else:
    cmd = ['bash', 'run_test.sh']

with open(os.path.join(log_dir, 'test_run.log'), 'wb') as f:
    proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    proc.wait()
    exit(proc.returncode)
