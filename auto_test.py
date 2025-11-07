#!/usr/bin/env python3
"""
Flask Security Audit - Automatic Test Runner
Detects the environment and runs appropriate tests with comprehensive logging
"""

import os
import sys
import subprocess
import platform
import time
import json
from datetime import datetime
import shutil

def detect_environment():
    """Detect the current environment (Windows/Linux/Docker)"""
    system = platform.system().lower()
    
    # Check if running in Docker
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
        return 'docker'
    elif system == 'windows':
        return 'windows'
    elif system in ['linux', 'darwin']:  # Darwin is macOS
        return 'unix'
    else:
        return 'unknown'

def setup_logging():
    """Setup logging directory and files"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'test_run_{timestamp}.log')
    
    return log_file

def log_message(message, log_file=None):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{timestamp}] {message}"
    
    print(formatted_message)
    
    if log_file:
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

def check_dependencies():
    """Check if required dependencies are available"""
    dependencies = {
        'python': ['python3', '--version'],
        'curl': ['curl', '--version'],
        'pip': ['pip', '--version']
    }
    
    missing = []
    for dep, cmd in dependencies.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                missing.append(dep)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing.append(dep)
    
    return missing

def install_dependencies():
    """Install Python dependencies"""
    try:
        log_message("Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to install dependencies: {e}")
        return False
    except subprocess.TimeoutExpired:
        log_message("Dependency installation timed out")
        return False

def run_unix_tests(log_file):
    """Run tests on Unix-like systems (Linux/macOS)"""
    log_message("Running Unix/Linux tests...", log_file)
    
    # Make script executable
    script_path = './run_test.sh'
    if os.path.exists(script_path):
        os.chmod(script_path, 0o755)
        
        try:
            result = subprocess.run(['bash', script_path], 
                                  capture_output=True, text=True, timeout=300)
            
            log_message(f"Test script output:\n{result.stdout}", log_file)
            if result.stderr:
                log_message(f"Test script errors:\n{result.stderr}", log_file)
            
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            log_message("Test execution timed out", log_file)
            return False
        except Exception as e:
            log_message(f"Error running tests: {e}", log_file)
            return False
    else:
        log_message("Unix test script not found", log_file)
        return False

def run_windows_tests(log_file):
    """Run tests on Windows"""
    log_message("Running Windows tests...", log_file)
    
    script_path = 'run_test.bat'
    if os.path.exists(script_path):
        try:
            result = subprocess.run([script_path], 
                                  shell=True, capture_output=True, text=True, timeout=300)
            
            log_message(f"Test script output:\n{result.stdout}", log_file)
            if result.stderr:
                log_message(f"Test script errors:\n{result.stderr}", log_file)
            
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            log_message("Test execution timed out", log_file)
            return False
        except Exception as e:
            log_message(f"Error running tests: {e}", log_file)
            return False
    else:
        log_message("Windows test script not found", log_file)
        return False

def run_docker_tests(log_file):
    """Run tests inside a Docker container environment by invoking local test script."""
    log_message("Running Docker tests...", log_file)

    try:
        # Use local test runner inside the container (no nested Docker required)
        log_message("Executing local tests inside container...", log_file)
        run_result = subprocess.run([
            sys.executable, 'local_tests.py', 'both', 'repaired'
        ], capture_output=True, text=True, timeout=300)

        log_message(f"Local test output:\n{run_result.stdout}", log_file)
        if run_result.stderr:
            log_message(f"Local test errors:\n{run_result.stderr}", log_file)

        return run_result.returncode == 0

    except subprocess.TimeoutExpired:
        log_message("Container test execution timed out", log_file)
        return False
    except Exception as e:
        log_message(f"Error running container tests: {e}", log_file)
        return False

def generate_test_report(success, environment, log_file, start_time):
    """Generate a comprehensive test report"""
    end_time = time.time()
    duration = end_time - start_time
    
    report = {
        'test_execution': {
            'timestamp': datetime.now().isoformat(),
            'environment': environment,
            'duration_seconds': round(duration, 2),
            'success': success,
            'log_file': log_file
        },
        'system_info': {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        },
        'files_generated': [
            'report.json',
            'input_secure.py',
            'requirements.txt',
            'Dockerfile',
            'setup.sh',
            'run_test.sh',
            'run_test.bat',
            'auto_test.py'
        ]
    }
    
    report_file = os.path.join('logs', 'test_execution_report.json')
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_message(f"Test execution report saved to: {report_file}", log_file)
    except Exception as e:
        log_message(f"Could not save test report: {e}", log_file)

def main():
    """Main function to orchestrate the testing process"""
    start_time = time.time()
    log_file = setup_logging()
    
    log_message("=== Flask Security Audit - Automatic Test Runner ===", log_file)
    log_message(f"Started at: {datetime.now().isoformat()}", log_file)
    
    # Detect environment
    environment = detect_environment()
    log_message(f"Detected environment: {environment}", log_file)
    log_message(f"System: {platform.system()} {platform.release()}", log_file)
    log_message(f"Python: {platform.python_version()}", log_file)
    
    # Check dependencies
    log_message("Checking dependencies...", log_file)
    missing_deps = check_dependencies()
    if missing_deps:
        log_message(f"Missing dependencies: {', '.join(missing_deps)}", log_file)
        log_message("Please install missing dependencies and try again.", log_file)
        generate_test_report(False, environment, log_file, start_time)
        return 1
    
    log_message("All dependencies found", log_file)
    
    # Install Python dependencies if needed
    if os.path.exists('requirements.txt'):
        if not install_dependencies():
            log_message("Failed to install Python dependencies", log_file)
            generate_test_report(False, environment, log_file, start_time)
            return 1
    
    # Run tests based on environment
    success = False
    
    if environment == 'docker':
        success = run_docker_tests(log_file)
    elif environment == 'windows':
        success = run_windows_tests(log_file)
    elif environment == 'unix':
        success = run_unix_tests(log_file)
    else:
        log_message(f"Unsupported environment: {environment}", log_file)
        generate_test_report(False, environment, log_file, start_time)
        return 1
    
    # Generate final report
    log_message("=" * 50, log_file)
    if success:
        log_message("ALL TESTS COMPLETED SUCCESSFULLY", log_file)
        log_message("Security fixes are working correctly!", log_file)
    else:
        log_message("TESTS FAILED", log_file)
        log_message("Please review the security implementation", log_file)
    
    log_message(f"Completed at: {datetime.now().isoformat()}", log_file)
    log_message(f"Total duration: {time.time() - start_time:.2f} seconds", log_file)
    log_message(f"Full log saved to: {log_file}", log_file)
    
    generate_test_report(success, environment, log_file, start_time)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())