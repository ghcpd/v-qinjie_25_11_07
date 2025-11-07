import sys, os, platform

def run_script(cmd):
    print('Running:', cmd)
    rc = os.system(cmd)
    if rc != 0:
        raise SystemExit(rc)

if __name__ == '__main__':
    plt = platform.system()
    if plt == 'Windows':
        run_script('python -m pytest -q')
    else:
        run_script('python -m pytest -q')
    print('Tests completed successfully')
