#!/usr/bin/env python3
"""
Automatic test execution script
Detects the current environment and runs the appropriate test script
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "test_run.log"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def detect_environment():
    """Detect the current execution environment"""
    system = platform.system().lower()
    
    # Check if running in Docker
    if os.path.exists('/.dockerenv') or os.path.exists('/proc/self/cgroup'):
        try:
            with open('/proc/self/cgroup', 'r') as f:
                if 'docker' in f.read():
                    return 'docker'
        except:
            pass
    
    # Check for WSL (Windows Subsystem for Linux)
    if 'microsoft' in platform.uname().release.lower():
        return 'wsl'
    
    # Detect OS
    if system == 'windows':
        return 'windows'
    elif system in ['linux', 'darwin']:
        return 'unix'
    else:
        return 'unknown'


def run_tests_unix():
    """Run tests on Unix-like systems (Linux/macOS)"""
    script_path = Path("run_test.sh")
    if not script_path.exists():
        logger.error(f"Test script not found: {script_path}")
        return False
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    logger.info("Running Unix test script...")
    try:
        result = subprocess.run(
            ['bash', str(script_path)],
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running test script: {e}")
        return False


def run_tests_windows():
    """Run tests on Windows"""
    script_path = Path("run_test.bat")
    if not script_path.exists():
        logger.error(f"Test script not found: {script_path}")
        return False
    
    logger.info("Running Windows test script...")
    try:
        result = subprocess.run(
            [str(script_path)],
            check=False,
            shell=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running test script: {e}")
        return False


def run_tests_docker():
    """Run tests in Docker container"""
    logger.info("Running tests in Docker container...")
    
    # Check if we're already in a container with the test script
    script_path = Path("run_test.sh")
    if script_path.exists():
        os.chmod(script_path, 0o755)
        try:
            result = subprocess.run(
                ['bash', str(script_path)],
                check=False,
                capture_output=False,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error running test script: {e}")
            return False
    else:
        logger.error("Test script not found in Docker container")
        return False


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Automatic Security Test Execution")
    logger.info("=" * 60)
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"System: {platform.system()}")
    logger.info(f"Python Version: {sys.version}")
    logger.info("")
    
    # Detect environment
    env = detect_environment()
    logger.info(f"Detected environment: {env}")
    logger.info("")
    
    # Run appropriate test script
    success = False
    if env == 'docker':
        success = run_tests_docker()
    elif env == 'windows':
        success = run_tests_windows()
    elif env in ['unix', 'wsl']:
        success = run_tests_unix()
    else:
        logger.warning(f"Unknown environment: {env}")
        logger.info("Attempting Unix test script as fallback...")
        success = run_tests_unix()
    
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("Test execution completed successfully")
        logger.info(f"Logs saved to: {LOG_FILE}")
        sys.exit(0)
    else:
        logger.error("Test execution completed with errors")
        logger.info(f"Check logs at: {LOG_FILE}")
        sys.exit(1)


if __name__ == '__main__':
    main()

